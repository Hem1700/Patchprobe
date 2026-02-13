from __future__ import annotations

import json
from pathlib import Path

from ..errors import ReportError
from ..utils.time import now_iso
from .artifacts import write_artifact
from .job import load_job


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    fmt = args.format or cfg.get("report", {}).get("format", "markdown")
    out_dir = Path(args.job) / "artifacts" / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "summary": "Placeholder report. Full report synthesis pending.",
        "candidates": [],
        "audit": [],
    }
    if fmt == "markdown":
        out_path = Path(args.job) / "report.md"
        out_path.write_text(
            f"# Patchdiff Report\n\n"
            f"Job: {job.job_id}\n\n"
            f"Summary: {report_payload['summary']}\n",
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
