from __future__ import annotations

import json
from pathlib import Path

from ..errors import ReportError
from ..utils.time import now_iso
from .artifacts import write_artifact
from .job import load_job


def _load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    fmt = args.format or cfg.get("report", {}).get("format", "markdown")
    out_dir = Path(args.job) / "artifacts" / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    ranked = _load_json(Path(args.job) / "artifacts" / "rank" / "ranked_candidates.json", default={})
    ranked_candidates = ranked.get("candidates", []) if isinstance(ranked, dict) else []
    if not isinstance(ranked_candidates, list):
        ranked_candidates = []
    llm = _load_json(Path(args.job) / "artifacts" / "analysis" / "llm.json", default={})
    analyses = llm.get("analysis", []) if isinstance(llm, dict) else []
    if not isinstance(analyses, list):
        analyses = []
    validation = _load_json(Path(args.job) / "artifacts" / "validation" / "validation_details.json", default={})
    validation_candidates = validation.get("candidates", []) if isinstance(validation, dict) else []
    if not isinstance(validation_candidates, list):
        validation_candidates = []

    analysis_by_pair = {a.get("func_pair_id"): a for a in analyses if isinstance(a, dict)}
    validation_by_pair = {v.get("func_pair_id"): v for v in validation_candidates if isinstance(v, dict)}
    report_candidates: list[dict] = []
    for candidate in ranked_candidates:
        if not isinstance(candidate, dict):
            continue
        func_pair_id = candidate.get("func_pair_id")
        if not isinstance(func_pair_id, str):
            continue
        analysis_item = analysis_by_pair.get(func_pair_id, {})
        validation_item = validation_by_pair.get(func_pair_id, {})
        rank_score = float(candidate.get("score", 0.0))
        llm_conf = float(analysis_item.get("confidence", 0.0)) if isinstance(analysis_item, dict) else 0.0
        val_score = float(validation_item.get("validation_score", 0.0)) if isinstance(validation_item, dict) else 0.0
        final_score = round((0.4 * rank_score) + (0.3 * llm_conf) + (0.3 * val_score), 6)
        report_candidates.append(
            {
                "func_pair_id": func_pair_id,
                "rank": candidate.get("rank"),
                "rank_score": rank_score,
                "llm_bug_class": analysis_item.get("bug_class"),
                "llm_confidence": llm_conf,
                "validation_score": val_score,
                "final_score": final_score,
                "top_signals": candidate.get("top_signals", []),
            }
        )

    report_candidates.sort(key=lambda item: item["final_score"], reverse=True)
    for idx, item in enumerate(report_candidates, start=1):
        item["final_rank"] = idx

    report_payload = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "summary": f"Analyzed {len(report_candidates)} candidate(s); top candidate selected by blended rank/LLM/validation score.",
        "candidates": report_candidates,
        "audit": [
            {"stage": "rank", "candidate_count": len(ranked_candidates)},
            {"stage": "analysis", "candidate_count": len(analyses)},
            {"stage": "validation", "candidate_count": len(validation_candidates)},
        ],
    }
    if fmt == "markdown":
        out_path = Path(args.job) / "report.md"
        lines = [
            "# Patchdiff Report",
            "",
            f"Job: {job.job_id}",
            "",
            f"Summary: {report_payload['summary']}",
            "",
            "## Top Candidates",
            "",
        ]
        if not report_candidates:
            lines.append("No candidates available.")
        else:
            for item in report_candidates[:10]:
                lines.append(
                    f"- `{item['func_pair_id']}` "
                    f"(final={item['final_score']:.3f}, rank={item['rank_score']:.3f}, "
                    f"llm={item['llm_confidence']:.3f}, validation={item['validation_score']:.3f}, "
                    f"class={item['llm_bug_class']})"
                )
        out_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
    elif fmt == "json":
        out_path = Path(args.job) / "report.json"
        out_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    else:
        raise ReportError(f"unsupported report format: {fmt}")

    write_artifact(
        out_dir / "report.artifact.json",
        "report.output",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        report_payload,
        payload_schema="report.schema.json",
        job_dir=Path(args.job),
    )
