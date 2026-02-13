from __future__ import annotations

import json
from pathlib import Path

from .artifacts import write_artifact
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
    write_artifact(
        out_dir / "ranked_candidates.artifact.json",
        "rank.candidates",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        ranked,
        job_dir=Path(args.job),
    )
