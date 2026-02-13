from __future__ import annotations

import json
from pathlib import Path

from .artifacts import write_artifact
from .job import load_job
from ..utils.time import now_iso


def _safe_decode_name(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()


def _parse_pe_sections(data: bytes) -> list[dict]:
    if len(data) < 0x40:
        return []
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if pe_offset + 24 > len(data):
        return []
    section_count = int.from_bytes(data[pe_offset + 6:pe_offset + 8], "little")
    opt_header_size = int.from_bytes(data[pe_offset + 20:pe_offset + 22], "little")
    section_table = pe_offset + 24 + opt_header_size
    sections: list[dict] = []
    for idx in range(section_count):
        off = section_table + (40 * idx)
        if off + 40 > len(data):
            break
        sections.append(
            {
                "name": _safe_decode_name(data[off:off + 8]),
                "virtual_size": int.from_bytes(data[off + 8:off + 12], "little"),
                "virtual_address": int.from_bytes(data[off + 12:off + 16], "little"),
                "raw_size": int.from_bytes(data[off + 16:off + 20], "little"),
                "raw_offset": int.from_bytes(data[off + 20:off + 24], "little"),
            }
        )
    return sections


def _parse_elf_sections(data: bytes) -> list[dict]:
    if len(data) < 0x40:
        return []
    ei_class = data[4]
    ei_data = data[5]
    endian = "little" if ei_data == 1 else "big"
    if ei_class == 1:
        e_shoff = int.from_bytes(data[32:36], endian)
        e_shentsize = int.from_bytes(data[46:48], endian)
        e_shnum = int.from_bytes(data[48:50], endian)
        e_shstrndx = int.from_bytes(data[50:52], endian)
        name_off = 0
        type_off = 4
        section_data_off = 16
        section_data_size = 20
    elif ei_class == 2:
        e_shoff = int.from_bytes(data[40:48], endian)
        e_shentsize = int.from_bytes(data[58:60], endian)
        e_shnum = int.from_bytes(data[60:62], endian)
        e_shstrndx = int.from_bytes(data[62:64], endian)
        name_off = 0
        type_off = 4
        section_data_off = 24
        section_data_size = 32
    else:
        return []

    if e_shoff <= 0 or e_shentsize <= 0 or e_shnum <= 0:
        return []
    if e_shoff + (e_shentsize * e_shnum) > len(data):
        return []
    if e_shstrndx >= e_shnum:
        return []

    def section_header(index: int) -> bytes:
        start = e_shoff + (index * e_shentsize)
        return data[start:start + e_shentsize]

    shstr_hdr = section_header(e_shstrndx)
    shstr_off = int.from_bytes(shstr_hdr[section_data_off:section_data_off + (8 if ei_class == 2 else 4)], endian)
    shstr_size = int.from_bytes(shstr_hdr[section_data_size:section_data_size + (8 if ei_class == 2 else 4)], endian)
    if shstr_off + shstr_size > len(data):
        return []
    shstr = data[shstr_off:shstr_off + shstr_size]

    def lookup_name(offset: int) -> str:
        if offset >= len(shstr):
            return ""
        end = shstr.find(b"\x00", offset)
        if end < 0:
            end = len(shstr)
        return shstr[offset:end].decode("ascii", errors="replace")

    sections: list[dict] = []
    for idx in range(e_shnum):
        hdr = section_header(idx)
        sh_name = int.from_bytes(hdr[name_off:name_off + 4], endian)
        sh_type = int.from_bytes(hdr[type_off:type_off + 4], endian)
        sh_off = int.from_bytes(hdr[section_data_off:section_data_off + (8 if ei_class == 2 else 4)], endian)
        sh_size = int.from_bytes(hdr[section_data_size:section_data_size + (8 if ei_class == 2 else 4)], endian)
        sections.append(
            {
                "name": lookup_name(sh_name),
                "type": sh_type,
                "offset": sh_off,
                "size": sh_size,
            }
        )
    return sections


def _pe_security_directory_present(data: bytes) -> bool:
    if len(data) < 0x40:
        return False
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    opt_offset = pe_offset + 24
    if opt_offset + 2 > len(data):
        return False
    magic = int.from_bytes(data[opt_offset:opt_offset + 2], "little")
    if magic == 0x10B:
        data_dir_offset = opt_offset + 96
    elif magic == 0x20B:
        data_dir_offset = opt_offset + 112
    else:
        return False
    security_dir = data_dir_offset + (8 * 4)
    if security_dir + 8 > len(data):
        return False
    security_size = int.from_bytes(data[security_dir + 4:security_dir + 8], "little")
    return security_size > 0


def _summarize_binary(path: Path, file_type: str, arch: str, sha256: str) -> dict:
    data = path.read_bytes()
    sections: list[dict] = []
    has_signature = False
    if file_type == "PE":
        sections = _parse_pe_sections(data)
        has_signature = _pe_security_directory_present(data)
    elif file_type == "ELF":
        sections = _parse_elf_sections(data)

    section_names = {s.get("name", "") for s in sections if s.get("name")}
    import_section_names = {".idata", ".plt", ".plt.sec", ".got", ".got.plt", "__stubs", "__la_symbol_ptr"}
    export_section_names = {".edata", ".dynsym", "__nl_symbol_ptr"}
    symbol_section_names = {".symtab", ".dynsym", "__symbol_table"}

    return {
        "path": str(path),
        "sha256": sha256,
        "file_type": file_type,
        "arch": arch,
        "size_bytes": len(data),
        "section_count": len(sections),
        "sections": sections,
        "has_imports_hint": bool(section_names & import_section_names),
        "has_exports_hint": bool(section_names & export_section_names),
        "has_symbols_hint": bool(section_names & symbol_section_names),
        "has_debug_info_hint": any(n.startswith(".debug") for n in section_names) or (b"RSDS" in data),
        "has_signature_hint": has_signature,
    }


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    out_dir = Path(args.job) / "artifacts" / "normalize"
    out_dir.mkdir(parents=True, exist_ok=True)

    binary_a = _summarize_binary(Path(job.binary_a.path), job.binary_a.file_type, job.binary_a.arch, job.binary_a.sha256)
    binary_b = _summarize_binary(Path(job.binary_b.path), job.binary_b.file_type, job.binary_b.arch, job.binary_b.sha256)
    normalized = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "binary_a": binary_a,
        "binary_b": binary_b,
        "delta": {
            "size_bytes": binary_b["size_bytes"] - binary_a["size_bytes"],
            "section_count": binary_b["section_count"] - binary_a["section_count"],
        },
    }
    (out_dir / "normalized_metadata.json").write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    write_artifact(
        out_dir / "normalized_metadata.artifact.json",
        "normalize.metadata",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        normalized,
        job_dir=Path(args.job),
    )
