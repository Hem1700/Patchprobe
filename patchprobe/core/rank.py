from __future__ import annotations

import json
from pathlib import Path

from .job import load_job
from ..utils.time import now_iso


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    top_n = args.top or cfg.get("ranking", {}).get("top_n", 30)

    out_dir = Path(args.job) / "artifacts" / "rank"
    out_dir.mkdir(parents=True, exist_ok=True)

    ranked = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "top_n": top_n,
        "candidates": [],
    }
    (out_dir / "ranked_candidates.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")
