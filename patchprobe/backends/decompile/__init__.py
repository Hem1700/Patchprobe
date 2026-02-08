from .base import DecompileBackend
from .ghidra_headless import GhidraHeadlessBackend


def get_backend(name: str) -> DecompileBackend:
    name = name.lower()
    if name in {"ghidra", "ghidra_headless"}:
        return GhidraHeadlessBackend()
    raise ValueError(f"Unknown decompile backend: {name}")
