from __future__ import annotations

from .job import load_job
from ..backends.decompile import get_backend


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    backend_name = cfg.get("backends", {}).get("decompile", "ghidra")
    top_n = args.top or cfg.get("ranking", {}).get("top_n")
    backend = get_backend(backend_name)
    backend.run(job, args.job, top_n=top_n, timeout=args.timeout)
