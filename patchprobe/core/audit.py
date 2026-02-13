from __future__ import annotations

import json
from pathlib import Path

from ..utils.time import now_iso


def append_audit_entry(job_dir: str, stage: str, event: str, details: dict | None = None) -> None:
    path = Path(job_dir) / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": now_iso(),
        "stage": stage,
        "event": event,
        "details": details or {},
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
