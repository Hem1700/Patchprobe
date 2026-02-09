from pathlib import Path

from patchprobe.config import load_config, resolve_config_path
from patchprobe.constants import ENV_CONFIG_PATH, ENV_OFFLINE


def test_env_config_path(monkeypatch, tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("report:\n  format: json\n", encoding="utf-8")
    monkeypatch.setenv(ENV_CONFIG_PATH, str(cfg))
    path = resolve_config_path(None)
    assert path == cfg
    data = load_config(None)
    assert data["report"]["format"] == "json"


def test_offline_override(monkeypatch, tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("llm:\n  provider: openai\n", encoding="utf-8")
    monkeypatch.setenv(ENV_OFFLINE, "1")
    data = load_config(str(cfg))
    assert data["llm"]["provider"] == "local"
