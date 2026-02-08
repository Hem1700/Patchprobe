from .base import DiffBackend
from .diaphora import DiaphoraBackend
from .ghidra_diff import GhidraDiffBackend
from .radare2 import Radare2Backend


def get_backend(name: str) -> DiffBackend:
    name = name.lower()
    if name == "diaphora":
        return DiaphoraBackend()
    if name in {"ghidra", "ghidra_diff"}:
        return GhidraDiffBackend()
    if name in {"radare2", "radare"}:
        return Radare2Backend()
    raise ValueError(f"Unknown diff backend: {name}")
