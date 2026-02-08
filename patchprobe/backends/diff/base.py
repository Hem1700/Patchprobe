from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ...core.job import Job


@dataclass
class AnalysisArtifact:
    path: str
    tool: str
    notes: str


@dataclass
class FunctionPair:
    func_pair_id: str
    func_id_a: str
    func_id_b: str
    match_score: float
    status: str
    evidence: list[str]


@dataclass
class DiffResult:
    func_pair_id: str
    change_summary: dict
    severity_hint: float


class DiffBackend(Protocol):
    def run(self, job: Job, job_dir: str) -> None:
        ...
