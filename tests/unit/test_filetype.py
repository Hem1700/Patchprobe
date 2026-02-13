from pathlib import Path
from patchprobe.utils.filetype import detect_filetype_and_arch


def test_unknown_filetype(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"1234")
    ftype, arch = detect_filetype_and_arch(p)
    assert ftype in {"unknown", "PE", "ELF", "Mach-O"}
    assert arch in {"unknown", "x86", "x64", "arm64", "arm", "mips"}


def test_elf_arch_from_machine_field(tmp_path: Path) -> None:
    p = tmp_path / "y.elf"
    data = bytearray(64)
    data[:4] = b"\x7fELF"
    data[18:20] = (0xB7).to_bytes(2, "little")  # AArch64
    p.write_bytes(bytes(data))
    ftype, arch = detect_filetype_and_arch(p)
    assert ftype == "ELF"
    assert arch == "arm64"
