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


def _score_candidate(function_pair: dict, diff_result: dict, weights: dict) -> tuple[float, list[dict]]:
    severity = float(diff_result.get("severity_hint", 0.0))
    match = float(function_pair.get("match_score", 0.0))
    evidence_count = len(function_pair.get("evidence", []))
    evidence_score = min(evidence_count, 5) / 5.0
    w_severity = float(weights.get("severity_hint", 0.6))
    w_match = float(weights.get("match_score", 0.3))
    w_evidence = float(weights.get("evidence", 0.1))
    score = (w_severity * severity) + (w_match * match) + (w_evidence * evidence_score)
    top_signals = [
        {"signal": "severity_hint", "evidence": str(severity)},
        {"signal": "match_score", "evidence": str(match)},
        {"signal": "evidence_count", "evidence": str(evidence_count)},
    ]
    return score, top_signals


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    top_n = args.top or cfg.get("ranking", {}).get("top_n", 30)
    weights = cfg.get("ranking", {}).get("weights", {}) or {}

    out_dir = Path(args.job) / "artifacts" / "rank"
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_dir = Path(args.job) / "artifacts" / "diff"
    function_pairs = _load_json(diff_dir / "function_pairs.json", default=[])
    diff_results = _load_json(diff_dir / "diff_results.json", default=[])
    if not isinstance(function_pairs, list):
        function_pairs = []
    if not isinstance(diff_results, list):
        diff_results = []

    diff_by_pair = {d.get("func_pair_id"): d for d in diff_results if isinstance(d, dict)}
    ranked_candidates: list[dict] = []
    for pair in function_pairs:
        if not isinstance(pair, dict):
            continue
        func_pair_id = pair.get("func_pair_id")
        if not func_pair_id:
            continue
        diff_result = diff_by_pair.get(func_pair_id, {})
        score, top_signals = _score_candidate(pair, diff_result, weights)
        ranked_candidates.append(
            {
                "func_pair_id": func_pair_id,
                "rank": 0,
                "score": round(score, 6),
                "top_signals": top_signals,
            }
        )

    ranked_candidates.sort(key=lambda item: item["score"], reverse=True)
    ranked_candidates = ranked_candidates[:top_n]
    for idx, candidate in enumerate(ranked_candidates, start=1):
        candidate["rank"] = idx

    ranked = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "top_n": top_n,
        "candidates": ranked_candidates,
    }
    (out_dir / "ranked_candidates.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    write_artifact(
        out_dir / "ranked_candidates.artifact.json",
        "rank.candidates",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        ranked_candidates,
        payload_schema="ranked_candidate.schema.json",
        payload_is_list=True,
        job_dir=Path(args.job),
    )
