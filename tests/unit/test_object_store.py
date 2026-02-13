from pathlib import Path

from patchprobe.storage.object_store import FilesystemObjectStore, get_object_store


def test_filesystem_object_store_put_get_exists(tmp_path: Path) -> None:
    store = FilesystemObjectStore(root=str(tmp_path))
    store.put("a/b.bin", b"abc")
    assert store.exists("a/b.bin")
    assert store.get("a/b.bin") == b"abc"


def test_get_object_store_filesystem(tmp_path: Path) -> None:
    cfg = {"storage": {"type": "filesystem", "root": str(tmp_path)}}
    store = get_object_store(cfg)
    store.put("x.txt", b"1")
    assert store.get("x.txt") == b"1"
