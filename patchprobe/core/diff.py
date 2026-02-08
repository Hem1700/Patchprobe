from __future__ import annotations

from .job import load_job
from ..backends.diff import get_backend


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    backend_name = args.backend or cfg.get("backends", {}).get("diff", "diaphora")
    backend = get_backend(backend_name)
    backend.run(job, args.job)
