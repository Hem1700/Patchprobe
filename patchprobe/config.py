from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .constants import DEFAULT_CONFIG_PATH, DEFAULT_TOP_N


@dataclass
class Config:
    storage: dict = field(default_factory=lambda: {"type": "filesystem", "root": "~/.patchdiff"})
    backends: dict = field(default_factory=lambda: {"diff": "diaphora", "decompile": "ghidra", "llm": "local"})
    ranking: dict = field(default_factory=lambda: {"top_n": DEFAULT_TOP_N, "weights": {}})
    llm: dict = field(default_factory=lambda: {"provider": "local", "model": "llama3", "max_rounds": 1})
    report: dict = field(default_factory=lambda: {"format": "markdown"})


def load_config(path: str | None = None) -> dict:
    cfg_path = Path(os.path.expanduser(path or DEFAULT_CONFIG_PATH))
    if not cfg_path.exists():
        return Config().__dict__
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    base = Config().__dict__
    return merge_dicts(base, data)


def merge_dicts(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = merge_dicts(base[k], v)
        else:
            base[k] = v
    return base
