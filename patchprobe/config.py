from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

from .constants import DEFAULT_CONFIG_PATH, DEFAULT_TOP_N, ENV_CONFIG_PATH, ENV_OFFLINE
from .errors import ConfigError
from .utils.jsonschema import validate_data


@dataclass
class Config:
    storage: dict = field(default_factory=lambda: {"type": "filesystem", "root": "~/.patchdiff"})
    backends: dict = field(default_factory=lambda: {"diff": "diaphora", "decompile": "ghidra", "llm": "local"})
    ranking: dict = field(default_factory=lambda: {"top_n": DEFAULT_TOP_N, "weights": {}})
    llm: dict = field(default_factory=lambda: {"provider": "local", "model": "llama3", "max_rounds": 1})
    report: dict = field(default_factory=lambda: {"format": "markdown"})


CONFIG_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "specs" / "schemas" / "config.schema.json"
_TRUTHY = {"1", "true", "yes", "on"}


def resolve_config_path(path: str | None = None) -> Path:
    env_path = os.environ.get(ENV_CONFIG_PATH)
    selected = path or env_path or DEFAULT_CONFIG_PATH
    return Path(os.path.expanduser(selected))


def load_config(path: str | None = None) -> dict:
    cfg_path = resolve_config_path(path)
    base = Config().__dict__
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        base = merge_dicts(base, data)
    return apply_env_overrides(base)


def merge_dicts(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = merge_dicts(base[k], v)
        else:
            base[k] = v
    return base


def apply_env_overrides(cfg: dict, env: Mapping[str, str] | None = None) -> dict:
    env = env or os.environ
    offline = env.get(ENV_OFFLINE)
    if offline and offline.strip().lower() in _TRUTHY:
        cfg.setdefault("llm", {})["provider"] = "local"
    return cfg


def validate_config(cfg: dict, schema_path: Path | None = None) -> None:
    schema = schema_path or CONFIG_SCHEMA_PATH
    if not schema.exists():
        raise ConfigError("config schema not found", details={"path": str(schema)})
    try:
        validate_data(str(schema), cfg)
    except Exception as e:  # noqa: BLE001
        raise ConfigError("config validation failed", details={"error": str(e)})
