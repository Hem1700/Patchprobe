from __future__ import annotations

import os
from pathlib import Path


def expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def job_root(path: str) -> Path:
    return expand(path)


def artifacts_dir(job_dir: str) -> Path:
    return job_root(job_dir) / "artifacts"


def logs_dir(job_dir: str) -> Path:
    return job_root(job_dir) / "logs"
