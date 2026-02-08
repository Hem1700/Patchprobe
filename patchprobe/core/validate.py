from __future__ import annotations

import json
from pathlib import Path

from .job import load_job
from ..utils.time import now_iso


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    out_dir = Path(args.job) / "artifacts" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "checks": [],
    }
    (out_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
