from __future__ import annotations

from pathlib import Path

from .job import load_job


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    fmt = args.format or cfg.get("report", {}).get("format", "markdown")

    out_path = Path(args.job) / ("report.md" if fmt == "markdown" else "report.json")
    out_path.write_text(f"# Patchdiff Report

Job: {job.job_id}
", encoding="utf-8")
