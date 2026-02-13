from __future__ import annotations

from pathlib import Path


def extract_build_id(path: Path, file_type: str) -> str | None:
    data = path.read_bytes()
    if file_type == "ELF":
        return _extract_elf_build_id(data)
    if file_type == "PE":
        return _extract_pe_debug_id(data)
    return None


def _extract_elf_build_id(data: bytes) -> str | None:
    marker = b"GNU\x00"
    idx = data.find(marker)
    if idx < 0:
        return None
    # Heuristic: build-id bytes follow ELF GNU note payload. Read up to 20 bytes.
    start = idx + len(marker)
    candidate = data[start:start + 20]
    if len(candidate) < 8:
        return None
    return candidate.hex()


def _extract_pe_debug_id(data: bytes) -> str | None:
    idx = data.find(b"RSDS")
    if idx < 0 or idx + 24 > len(data):
        return None
    guid_age = data[idx + 4:idx + 24]
    if len(guid_age) != 20:
        return None
    return guid_age.hex()
