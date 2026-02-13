from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from ..constants import VERSION
from ..utils.hashing import sha256_file
from ..utils.time import now_iso
from ..utils.jsonschema import validate_data, validate_instance

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "specs" / "schemas"
ARTIFACT_SCHEMA_PATH = SCHEMAS_DIR / "artifact.schema.json"


def _sha256_json(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _infer_job_dir(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.name == "artifacts":
            return parent.parent
    return None


def _update_artifact_index(job_dir: Path, artifact_entry: dict) -> None:
    index_path = job_dir / "artifact_index.json"
    index = []
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    index.append(artifact_entry)
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _validate_payload(payload: object, payload_schema: str | None, payload_is_list: bool) -> None:
    if not payload_schema:
        return
    schema_path = SCHEMAS_DIR / payload_schema
    if payload_is_list:
        if not isinstance(payload, list):
            raise TypeError("payload must be a list when payload_is_list=True")
        for item in payload:
            validate_instance(str(schema_path), item)
        return
    validate_instance(str(schema_path), payload)


def write_artifact(
    path: Path,
    artifact_type: str,
    inputs: dict,
    payload: object,
    *,
    payload_schema: str | None = None,
    payload_is_list: bool = False,
    job_dir: Path | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _validate_payload(payload, payload_schema, payload_is_list)
    payload_sha256 = _sha256_json(payload)
    envelope = {
        "artifact_id": str(uuid.uuid4()),
        "artifact_type": artifact_type,
        "created_at": now_iso(),
        "tool_version": VERSION,
        "inputs": inputs,
        "payload_sha256": payload_sha256,
        "payload": payload,
    }
    validate_data(str(ARTIFACT_SCHEMA_PATH), envelope)
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    artifact_sha256 = sha256_file(path)

    actual_job_dir = job_dir or _infer_job_dir(path)
    if actual_job_dir:
        _update_artifact_index(
            actual_job_dir,
            {
                "artifact_id": envelope["artifact_id"],
                "artifact_type": artifact_type,
                "created_at": envelope["created_at"],
                "path": str(path),
                "payload_sha256": payload_sha256,
                "artifact_sha256": artifact_sha256,
            },
        )
