from __future__ import annotations

import json
from pathlib import Path

from .job import load_job
from ..backends.llm import get_provider
from ..utils.time import now_iso


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    provider_name = args.provider or cfg.get("llm", {}).get("provider", "local")
    model = args.model or cfg.get("llm", {}).get("model", "llama3")
    max_rounds = args.max_rounds or cfg.get("llm", {}).get("max_rounds", 1)

    provider = get_provider(provider_name, model=model, max_rounds=max_rounds)

    out_dir = Path(args.job) / "artifacts" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Placeholder: no real packets yet
    output = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "analysis": [],
    }
    (out_dir / "llm.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
