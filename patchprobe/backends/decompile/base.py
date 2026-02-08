from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ...core.job import Job


@dataclass
class DecompileArtifact:
    func_id: str
    pseudocode: str
    prototype: str | None
    callers: list[str]
    callees: list[str]
    status: str


class DecompileBackend(Protocol):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        ...
