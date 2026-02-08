from pathlib import Path
from patchprobe.utils.hashing import sha256_file


def test_sha256_file(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("abc", encoding="utf-8")
    h = sha256_file(p)
    assert len(h) == 64
