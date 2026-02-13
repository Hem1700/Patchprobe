import json
from argparse import Namespace
from pathlib import Path

from patchprobe.core.job import BinaryInfo, create_job
from patchprobe.core.validate import run as run_validate


def test_validate_stage_generates_checks_and_candidate_scores(tmp_path: Path) -> None:
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
    (diff_dir / "function_pairs.json").write_text(
        json.dumps([{"func_pair_id": "fp1", "func_id_a": "fa1", "func_id_b": "fb1", "match_score": 1.0, "status": "ok", "evidence": []}]),
        encoding="utf-8",
    )
    (diff_dir / "diff_results.json").write_text(
        json.dumps([{"func_pair_id": "fp1", "change_summary": {"note": "bounds check"}, "severity_hint": 0.7}]),
        encoding="utf-8",
    )

    decompile_dir = job_dir / "artifacts" / "decompile"
    decompile_dir.mkdir(parents=True, exist_ok=True)
    (decompile_dir / "decompile_artifacts.json").write_text(
        json.dumps(
            [
                {"func_id": "fa1", "binary_sha": "a" * 64, "prototype": "int main(void)", "pseudocode": "int main(){return 0;}", "callers": [], "callees": [], "strings": [], "status": "ok", "error": None},
                {"func_id": "fb1", "binary_sha": "b" * 64, "prototype": "int main(void)", "pseudocode": "int main(){/* bounds check */return 0;}", "callers": [], "callees": [], "strings": [], "status": "ok", "error": None},
            ]
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
                    {
                        "func_pair_id": "fp1",
                        "bug_class": "bounds-check-hardening",
                        "confidence": 0.8,
                        "evidence": [{"type": "diff_summary", "snippet": "bounds check", "location": "diff.change_summary"}],
                        "reachability_notes": [],
                        "recommended_validation": [],
                        "safety": {"no_exploit_steps": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    run_validate({}, Namespace(job=str(job_dir)))

    validation = json.loads((job_dir / "artifacts" / "validation" / "validation.json").read_text(encoding="utf-8"))
    details = json.loads((job_dir / "artifacts" / "validation" / "validation_details.json").read_text(encoding="utf-8"))
    assert len(validation["checks"]) >= 3
    assert len(details["candidates"]) == 1
    assert details["candidates"][0]["bug_class_passed"] is True
    assert details["candidates"][0]["validation_score"] > 0.0
