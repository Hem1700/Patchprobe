from __future__ import annotations

from pathlib import Path

from .base import DecompileBackend
from ...core.job import Job


class GhidraHeadlessBackend(DecompileBackend):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        out_dir = Path(job_dir) / "artifacts" / "decompile"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Placeholder: actual Ghidra integration not yet implemented.
        (out_dir / "README.txt").write_text("Ghidra decompile backend placeholder", encoding="utf-8")
