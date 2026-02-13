from __future__ import annotations

from pathlib import Path

_ELF_MAGIC = b"\x7fELF"
_MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",  # MH_MAGIC
    b"\xce\xfa\xed\xfe",  # MH_CIGAM
    b"\xfe\xed\xfa\xcf",  # MH_MAGIC_64
    b"\xcf\xfa\xed\xfe",  # MH_CIGAM_64
    b"\xca\xfe\xba\xbe",  # FAT_MAGIC
    b"\xbe\xba\xfe\xca",  # FAT_CIGAM
}
_ELF_EM = {
    0x03: "x86",
    0x3E: "x64",
    0x28: "arm",
    0xB7: "arm64",
    0x08: "mips",
}
_MACHO_CPU = {
    0x00000007: "x86",
    0x01000007: "x64",
    0x0000000C: "arm",
    0x0100000C: "arm64",
}


def detect_filetype_and_arch(path: Path) -> tuple[str, str]:
    data = path.read_bytes()[:64]
    if data.startswith(b"MZ"):
        return "PE", _detect_pe_arch(path)
    if data.startswith(_ELF_MAGIC):
        return "ELF", _detect_elf_arch(data)
    if data[:4] in _MACHO_MAGICS:
        return "Mach-O", _detect_macho_arch(data)
    return "unknown", "unknown"


def _detect_pe_arch(path: Path) -> str:
    data = path.read_bytes()
    if len(data) < 0x3C + 4:
        return "unknown"
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if len(data) < pe_offset + 6:
        return "unknown"
    machine = int.from_bytes(data[pe_offset + 4:pe_offset + 6], "little")
    if machine == 0x14C:
        return "x86"
    if machine == 0x8664:
        return "x64"
    if machine == 0xAA64:
        return "arm64"
    return "unknown"


def _detect_elf_arch(data: bytes) -> str:
    if len(data) < 0x14:
        return "unknown"
    e_machine = int.from_bytes(data[18:20], "little")
    return _ELF_EM.get(e_machine, "unknown")


def _detect_macho_arch(data: bytes) -> str:
    if len(data) < 8:
        return "unknown"
    magic = data[:4]
    endian = "little" if magic in {b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe", b"\xbe\xba\xfe\xca"} else "big"
    cputype = int.from_bytes(data[4:8], endian, signed=False)
    return _MACHO_CPU.get(cputype, "unknown")
