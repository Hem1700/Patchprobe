import json
from argparse import Namespace
from pathlib import Path

from patchprobe.core.job import BinaryInfo, create_job
from patchprobe.core.rank import run


def test_rank_scores_and_orders_candidates(tmp_path: Path) -> None:
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
        {"func_pair_id": "fp1", "func_id_a": "fa1", "func_id_b": "fb1", "match_score": 1.0, "status": "ok", "evidence": ["x"]},
        {"func_pair_id": "fp2", "func_id_a": "fa2", "func_id_b": "fb2", "match_score": 0.5, "status": "ok", "evidence": ["x", "y"]},
    ]
    diff_results = [
        {"func_pair_id": "fp1", "change_summary": {}, "severity_hint": 0.1},
        {"func_pair_id": "fp2", "change_summary": {}, "severity_hint": 0.9},
    ]
    (diff_dir / "function_pairs.json").write_text(json.dumps(function_pairs), encoding="utf-8")
    (diff_dir / "diff_results.json").write_text(json.dumps(diff_results), encoding="utf-8")

    run(
        {"ranking": {"top_n": 10, "weights": {"severity_hint": 0.7, "match_score": 0.2, "evidence": 0.1}}},
        Namespace(job=str(job_dir), top=None),
    )

    ranked_path = job_dir / "artifacts" / "rank" / "ranked_candidates.json"
    ranked = json.loads(ranked_path.read_text(encoding="utf-8"))
    assert len(ranked["candidates"]) == 2
    assert ranked["candidates"][0]["func_pair_id"] == "fp2"
    assert ranked["candidates"][0]["rank"] == 1
    assert (job_dir / "artifacts" / "rank" / "ranked_candidates.artifact.json").exists()
