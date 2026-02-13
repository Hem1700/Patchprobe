import json
from argparse import Namespace
from pathlib import Path

from patchprobe.core.decompile import run as run_decompile
from patchprobe.core.job import BinaryInfo, create_job


def test_decompile_emits_per_function_artifacts_from_ranked_candidates(tmp_path: Path) -> None:
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"\x7fELF" + b"\x00" * 64)
    b.write_bytes(b"\x7fELF" + b"\x01" * 64)
    job_dir = tmp_path / "job"
    create_job(
        str(job_dir),
        None,
        BinaryInfo(path=str(a), sha256="a" * 64, file_type="ELF", arch="x64"),
        BinaryInfo(path=str(b), sha256="b" * 64, file_type="ELF", arch="x64"),
        {},
    )

    diff_dir = job_dir / "artifacts" / "diff"
    diff_dir.mkdir(parents=True, exist_ok=True)
    function_pairs = [
        {
            "func_pair_id": "fp1",
            "func_id_a": "fa1",
            "func_id_b": "fb1",
            "match_score": 1.0,
            "status": "matched_by_name",
            "evidence": ["symbol_name=main"],
        }
    ]
    (diff_dir / "function_pairs.json").write_text(json.dumps(function_pairs), encoding="utf-8")
    rank_dir = job_dir / "artifacts" / "rank"
    rank_dir.mkdir(parents=True, exist_ok=True)
    ranked = {"job_id": "job1", "created_at": "now", "top_n": 10, "candidates": [{"func_pair_id": "fp1", "rank": 1, "score": 0.9}]}
    (rank_dir / "ranked_candidates.json").write_text(json.dumps(ranked), encoding="utf-8")

    cfg = {"backends": {"decompile": "ghidra"}}
    args = Namespace(job=str(job_dir), top=1, timeout=7)
    run_decompile(cfg, args)

    out_dir = job_dir / "artifacts" / "decompile"
    artifacts = json.loads((out_dir / "decompile_artifacts.json").read_text(encoding="utf-8"))
    assert len(artifacts) == 2
    assert (out_dir / "fa1" / "metadata.json").exists()
    assert (out_dir / "fa1" / "pseudocode.txt").exists()
    assert (out_dir / "fb1" / "metadata.json").exists()
    assert (out_dir / "fb1" / "pseudocode.txt").exists()
