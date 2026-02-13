from __future__ import annotations

import json
from pathlib import Path

from .base import DecompileBackend
from ...core.artifacts import write_artifact
from ...core.job import Job


class GhidraHeadlessBackend(DecompileBackend):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        out_dir = Path(job_dir) / "artifacts" / "decompile"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Placeholder: actual Ghidra integration not yet implemented.
        (out_dir / "README.txt").write_text("Ghidra decompile backend placeholder", encoding="utf-8")
        artifacts: list[dict] = []
        (out_dir / "decompile_artifacts.json").write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
        write_artifact(
            out_dir / "decompile_artifacts.artifact.json",
            "decompile.artifacts",
            {
                "binary_a_sha256": job.binary_a.sha256,
                "binary_b_sha256": job.binary_b.sha256,
                "upstream_artifact_hashes": [],
            },
            artifacts,
            payload_schema="decompile_artifact.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
