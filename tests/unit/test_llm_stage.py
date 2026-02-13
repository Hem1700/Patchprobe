import json
from argparse import Namespace
from pathlib import Path

from patchprobe.core.job import BinaryInfo, create_job
from patchprobe.core.llm import run as run_llm


def test_llm_stage_builds_packets_and_analysis(tmp_path: Path) -> None:
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
        json.dumps(
            [
                {
                    "func_pair_id": "fp1",
                    "func_id_a": "fa1",
                    "func_id_b": "fb1",
                    "match_score": 1.0,
                    "status": "matched_by_name",
                    "evidence": ["symbol_name=main"],
                }
            ]
        ),
        encoding="utf-8",
    )
    (diff_dir / "diff_results.json").write_text(
        json.dumps([{"func_pair_id": "fp1", "change_summary": {"note": "bounds check"}, "severity_hint": 0.8}]),
        encoding="utf-8",
    )

    rank_dir = job_dir / "artifacts" / "rank"
    rank_dir.mkdir(parents=True, exist_ok=True)
    (rank_dir / "ranked_candidates.json").write_text(
        json.dumps({"job_id": "job1", "created_at": "now", "top_n": 10, "candidates": [{"func_pair_id": "fp1", "rank": 1, "score": 0.9}]}),
        encoding="utf-8",
    )

    decompile_dir = job_dir / "artifacts" / "decompile"
    decompile_dir.mkdir(parents=True, exist_ok=True)
    (decompile_dir / "decompile_artifacts.json").write_text(
        json.dumps(
            [
                {"func_id": "fa1", "binary_sha": "a" * 64, "prototype": "int main(void)", "pseudocode": "int main(void){return 0;}", "callers": [], "callees": [], "strings": [], "status": "ok", "error": None},
                {"func_id": "fb1", "binary_sha": "b" * 64, "prototype": "int main(void)", "pseudocode": "int main(void){if(x<y){return 0;}}", "callers": [], "callees": [], "strings": [], "status": "ok", "error": None},
            ]
        ),
        encoding="utf-8",
    )

    cfg = {"llm": {"provider": "local", "model": "llama3", "max_rounds": 3}}
    run_llm(cfg, Namespace(job=str(job_dir), provider=None, model=None, max_rounds=None))

    analysis_dir = job_dir / "artifacts" / "analysis"
    packets = json.loads((analysis_dir / "packets.json").read_text(encoding="utf-8"))
    round_outputs = json.loads((analysis_dir / "round_outputs.json").read_text(encoding="utf-8"))
    output = json.loads((analysis_dir / "llm.json").read_text(encoding="utf-8"))
    assert len(packets) == 1
    assert len(round_outputs) == 3
    assert len(output["analysis"]) == 1
    assert output["analysis"][0]["round_count"] == 3
    assert output["analysis"][0]["safety"]["no_exploit_steps"] is True
    assert (analysis_dir / "llm_outputs.artifact.json").exists()
