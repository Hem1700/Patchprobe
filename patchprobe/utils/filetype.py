from __future__ import annotations

from pathlib import Path


def detect_filetype_and_arch(path: Path) -> tuple[str, str]:
    data = path.read_bytes()[:64]
    if data.startswith(b"MZ"):
        return "PE", _detect_pe_arch(path)
    if data.startswith(b"ELF"):
        return "ELF", _detect_elf_arch(data)
    if data[:4] in {b"Ïúíþ", b"þíúÏ", b"Êþº¾", b"¾ºþÊ"}:
        return "Mach-O", "unknown"
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
    ei_class = data[4]
    if ei_class == 1:
        return "x86"
    if ei_class == 2:
        return "x64"
    return "unknown"
