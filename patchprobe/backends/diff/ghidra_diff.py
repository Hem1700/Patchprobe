from __future__ import annotations

import json
from pathlib import Path

from .base import DiffBackend
from ...core.job import Job
from ...core.artifacts import write_artifact


class GhidraDiffBackend(DiffBackend):
    def run(self, job: Job, job_dir: str) -> None:
        out_dir = Path(job_dir) / "artifacts" / "diff"
        out_dir.mkdir(parents=True, exist_ok=True)
        function_pairs: list[dict] = []
        diff_results: list[dict] = []
        (out_dir / "function_pairs.json").write_text(json.dumps(function_pairs, indent=2), encoding="utf-8")
        (out_dir / "diff_results.json").write_text(json.dumps(diff_results, indent=2), encoding="utf-8")
        inputs = {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        }
        write_artifact(
            out_dir / "function_pairs.artifact.json",
            "diff.function_pairs",
            inputs,
            function_pairs,
            payload_schema="function_pair.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
        write_artifact(
            out_dir / "diff_results.artifact.json",
            "diff.results",
            inputs,
            diff_results,
            payload_schema="diff_result.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
