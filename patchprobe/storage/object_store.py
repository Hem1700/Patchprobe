from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .filesystem_store import read_bytes, write_bytes


class ObjectStore(Protocol):
    def put(self, rel_path: str, data: bytes) -> str:
        ...

    def get(self, rel_path: str) -> bytes:
        ...

    def exists(self, rel_path: str) -> bool:
        ...


@dataclass
class FilesystemObjectStore:
    root: str

    def put(self, rel_path: str, data: bytes) -> str:
        return write_bytes(self.root, rel_path, data)

    def get(self, rel_path: str) -> bytes:
        return read_bytes(self.root, rel_path)

    def exists(self, rel_path: str) -> bool:
        return (Path(self.root) / rel_path).exists()


def get_object_store(cfg: dict) -> ObjectStore:
    storage = cfg.get("storage", {}) if isinstance(cfg, dict) else {}
    storage_type = str(storage.get("type", "filesystem")).lower()
    if storage_type != "filesystem":
        raise ValueError(f"unsupported storage type: {storage_type}")
    root = str(storage.get("root", "~/.patchdiff"))
    return FilesystemObjectStore(root=root)
