from argparse import Namespace
from pathlib import Path

from patchprobe.core import pipeline


def test_run_all_creates_normalize_outputs(tmp_path: Path) -> None:
    bin_a = tmp_path / "a.bin"
    bin_b = tmp_path / "b.bin"
    bin_a.write_bytes(b"\x7fELF" + b"\x00" * 128)
    bin_b.write_bytes(b"\x7fELF" + b"\x01" * 192)
    out = tmp_path / "job"

    args = Namespace(
        a=str(bin_a),
        b=str(bin_b),
        tag=None,
        out=str(out),
        backend=None,
        top=None,
        timeout=5,
        provider=None,
        model=None,
        max_rounds=None,
        format="json",
        job=None,
    )
    cfg = {
        "backends": {"diff": "diaphora", "decompile": "ghidra"},
        "llm": {"provider": "local", "model": "llama3", "max_rounds": 1},
        "report": {"format": "json"},
        "ranking": {"top_n": 10},
    }

    pipeline.run_all(cfg, args)

    assert (out / "artifacts" / "normalize" / "normalized_metadata.json").exists()
    assert (out / "artifact_index.json").exists()
