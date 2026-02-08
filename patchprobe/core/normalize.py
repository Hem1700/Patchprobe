from __future__ import annotations

import json
from pathlib import Path

from .job import load_job
from ..utils.time import now_iso


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    out_dir = Path(args.job) / "artifacts" / "normalize"
    out_dir.mkdir(parents=True, exist_ok=True)

    normalized = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "notes": "Normalization not yet implemented. Placeholder artifact.",
    }
    (out_dir / "normalized_metadata.json").write_text(json.dumps(normalized, indent=2), encoding="utf-8")
