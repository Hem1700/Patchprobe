from pathlib import Path
from patchprobe.utils.filetype import detect_filetype_and_arch


def test_unknown_filetype(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"1234")
    ftype, arch = detect_filetype_and_arch(p)
    assert ftype in {"unknown", "PE", "ELF", "Mach-O"}
    assert arch in {"unknown", "x86", "x64", "arm64"}
