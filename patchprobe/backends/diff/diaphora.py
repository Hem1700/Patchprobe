from __future__ import annotations

from pathlib import Path

from .base import DiffBackend
from ...core.job import Job


class DiaphoraBackend(DiffBackend):
    def run(self, job: Job, job_dir: str) -> None:
        out_dir = Path(job_dir) / "artifacts" / "diff"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Placeholder: actual Diaphora integration not yet implemented.
        (out_dir / "function_pairs.json").write_text("[]", encoding="utf-8")
        (out_dir / "diff_results.json").write_text("[]", encoding="utf-8")
