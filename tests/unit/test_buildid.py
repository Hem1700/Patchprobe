from pathlib import Path

from patchprobe.utils.buildid import extract_build_id


def test_extract_pe_debug_id_rsds(tmp_path: Path) -> None:
    p = tmp_path / "x.exe"
    payload = b"MZ" + b"\x00" * 64 + b"RSDS" + bytes(range(20)) + b"pdb\x00"
    p.write_bytes(payload)
    build_id = extract_build_id(p, "PE")
    assert build_id is not None
    assert len(build_id) == 40


def test_extract_elf_build_id_gnu_note_like(tmp_path: Path) -> None:
    p = tmp_path / "x.elf"
    payload = b"\x7fELF" + b"\x00" * 32 + b"GNU\x00" + bytes(range(20))
    p.write_bytes(payload)
    build_id = extract_build_id(p, "ELF")
    assert build_id is not None
    assert len(build_id) == 40
