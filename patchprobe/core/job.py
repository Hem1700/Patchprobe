from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils.time import now_iso


@dataclass
class BinaryInfo:
    path: str
    sha256: str
    file_type: str
    arch: str


@dataclass
class Job:
    job_id: str
    created_at: str
    tag: str | None
    binary_a: BinaryInfo
    binary_b: BinaryInfo
    config: dict


def create_job(out_dir: str, tag: str | None, binary_a: BinaryInfo, binary_b: BinaryInfo, config: dict) -> Job:
    job = Job(
        job_id=str(uuid.uuid4()),
        created_at=now_iso(),
        tag=tag,
        binary_a=binary_a,
        binary_b=binary_b,
        config=config,
    )
    path = Path(out_dir) / "job.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(job), f, indent=2)
    return job


def load_job(job_dir: str) -> Job:
    path = Path(job_dir) / "job.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    binary_a = BinaryInfo(**data["binary_a"])
    binary_b = BinaryInfo(**data["binary_b"])
    return Job(
        job_id=data["job_id"],
        created_at=data["created_at"],
        tag=data.get("tag"),
        binary_a=binary_a,
        binary_b=binary_b,
        config=data.get("config", {}),
    )
