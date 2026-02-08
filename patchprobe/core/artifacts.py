from __future__ import annotations

import json
import uuid
from pathlib import Path

from ..utils.time import now_iso


def write_artifact(path: Path, artifact_type: str, inputs: dict, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "artifact_id": str(uuid.uuid4()),
        "artifact_type": artifact_type,
        "created_at": now_iso(),
        "inputs": inputs,
        "payload": payload,
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
