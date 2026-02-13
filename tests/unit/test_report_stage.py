import json
from argparse import Namespace
from pathlib import Path

from patchprobe.core.job import BinaryInfo, create_job
from patchprobe.core.report import run as run_report


def test_report_stage_merges_rank_analysis_validation_and_orders_candidates(tmp_path: Path) -> None:
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

    rank_dir = job_dir / "artifacts" / "rank"
    rank_dir.mkdir(parents=True, exist_ok=True)
    (rank_dir / "ranked_candidates.json").write_text(
        json.dumps(
            {
                "job_id": "job1",
                "created_at": "now",
                "top_n": 10,
                "candidates": [
                    {"func_pair_id": "fp1", "rank": 1, "score": 0.6, "top_signals": []},
                    {"func_pair_id": "fp2", "rank": 2, "score": 0.9, "top_signals": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    analysis_dir = job_dir / "artifacts" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "llm.json").write_text(
        json.dumps(
            {
                "job_id": "job1",
                "created_at": "now",
                "analysis": [
                    {"func_pair_id": "fp1", "bug_class": "logic-fix", "confidence": 0.3, "evidence": [], "safety": {"no_exploit_steps": True}},
                    {"func_pair_id": "fp2", "bug_class": "bounds-check-hardening", "confidence": 0.7, "evidence": [], "safety": {"no_exploit_steps": True}},
                ],
            }
        ),
        encoding="utf-8",
    )
    validation_dir = job_dir / "artifacts" / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    (validation_dir / "validation_details.json").write_text(
        json.dumps(
            {
                "job_id": "job1",
                "created_at": "now",
                "candidates": [
                    {"func_pair_id": "fp1", "validation_score": 0.2},
                    {"func_pair_id": "fp2", "validation_score": 0.8},
                ],
            }
        ),
        encoding="utf-8",
    )

    run_report({"report": {"format": "json"}}, Namespace(job=str(job_dir), format="json"))

    report = json.loads((job_dir / "report.json").read_text(encoding="utf-8"))
    assert len(report["candidates"]) == 2
    assert report["candidates"][0]["func_pair_id"] == "fp2"
    assert report["candidates"][0]["final_rank"] == 1
