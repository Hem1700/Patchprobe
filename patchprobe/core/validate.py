from __future__ import annotations

import json
from pathlib import Path

from .artifacts import write_artifact
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
