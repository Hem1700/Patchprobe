from __future__ import annotations

import json
from pathlib import Path

from .artifacts import write_artifact
from .job import load_job
from ..utils.time import now_iso


def _load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence_present(snippet: str, decompile_a: dict, decompile_b: dict, diff_result: dict) -> bool:
    if not snippet:
        return False
    haystacks = [
        str(decompile_a.get("pseudocode", "")),
        str(decompile_b.get("pseudocode", "")),
        json.dumps(diff_result.get("change_summary", {}), sort_keys=True),
    ]
    needle = snippet.lower()
    return any(needle in h.lower() for h in haystacks)


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    out_dir = Path(args.job) / "artifacts" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    llm = _load_json(Path(args.job) / "artifacts" / "analysis" / "llm.json", default={})
    analyses = llm.get("analysis", []) if isinstance(llm, dict) else []
    if not isinstance(analyses, list):
        analyses = []
    decompile_items = _load_json(Path(args.job) / "artifacts" / "decompile" / "decompile_artifacts.json", default=[])
    diff_results = _load_json(Path(args.job) / "artifacts" / "diff" / "diff_results.json", default=[])
    function_pairs = _load_json(Path(args.job) / "artifacts" / "diff" / "function_pairs.json", default=[])
    if not isinstance(decompile_items, list):
        decompile_items = []
    if not isinstance(diff_results, list):
        diff_results = []
    if not isinstance(function_pairs, list):
        function_pairs = []

    decompile_by_func_id = {d.get("func_id"): d for d in decompile_items if isinstance(d, dict)}
    diff_by_pair = {d.get("func_pair_id"): d for d in diff_results if isinstance(d, dict)}
    pair_by_id = {p.get("func_pair_id"): p for p in function_pairs if isinstance(p, dict)}
    checks: list[dict] = []
    per_candidate: list[dict] = []
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        func_pair_id = analysis.get("func_pair_id")
        if not isinstance(func_pair_id, str):
            continue
        pair = pair_by_id.get(func_pair_id, {})
        diff_result = diff_by_pair.get(func_pair_id, {})
        func_id_a = pair.get("func_id_a")
        func_id_b = pair.get("func_id_b")
        decomp_a = decompile_by_func_id.get(func_id_a, {}) if isinstance(func_id_a, str) else {}
        decomp_b = decompile_by_func_id.get(func_id_b, {}) if isinstance(func_id_b, str) else {}
        evidence_items = analysis.get("evidence", [])
        evidence_passed = True
        if isinstance(evidence_items, list):
            for item in evidence_items:
                if not isinstance(item, dict):
                    evidence_passed = False
                    continue
                snippet = str(item.get("snippet", ""))
                if not _evidence_present(snippet, decomp_a, decomp_b, diff_result):
                    evidence_passed = False
        else:
            evidence_passed = False
            evidence_items = []

        safety_passed = bool(analysis.get("safety", {}).get("no_exploit_steps", False))
        confidence = float(analysis.get("confidence", 0.0))
        score = (
            (0.5 if evidence_passed else 0.0)
            + (0.2 if safety_passed else 0.0)
            + min(max(confidence, 0.0), 1.0) * 0.3
        )
        score = round(score, 6)
        checks.append(
            {
                "name": f"{func_pair_id}:evidence_present",
                "passed": evidence_passed,
                "evidence": f"evidence_items={len(evidence_items)}",
            }
        )
        checks.append(
            {
                "name": f"{func_pair_id}:safety_flag",
                "passed": safety_passed,
                "evidence": f"no_exploit_steps={safety_passed}",
            }
        )
        per_candidate.append(
            {
                "func_pair_id": func_pair_id,
                "evidence_passed": evidence_passed,
                "safety_passed": safety_passed,
                "validation_score": score,
            }
        )

    validation = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "checks": checks,
    }
    (out_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    details = {
        "job_id": job.job_id,
        "created_at": validation["created_at"],
        "candidates": per_candidate,
    }
    (out_dir / "validation_details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    write_artifact(
        out_dir / "validation.artifact.json",
        "validation.result",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        validation,
        payload_schema="validation_result.schema.json",
        job_dir=Path(args.job),
    )
