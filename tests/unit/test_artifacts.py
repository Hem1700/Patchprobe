import json
from pathlib import Path

from patchprobe.core.artifacts import write_artifact


def test_write_artifact_creates_envelope_and_index(tmp_path: Path) -> None:
    job_dir = tmp_path / "job1"
    artifact_path = job_dir / "artifacts" / "ingest" / "metadata.artifact.json"
    inputs = {
        "binary_a_sha256": "a" * 64,
        "binary_b_sha256": "b" * 64,
        "upstream_artifact_hashes": [],
    }
    payload = {"x": 1}

    write_artifact(artifact_path, "ingest.metadata", inputs, payload, job_dir=job_dir)

    assert artifact_path.exists()
    envelope = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert envelope["artifact_type"] == "ingest.metadata"
    assert envelope["inputs"]["binary_a_sha256"] == "a" * 64
    assert envelope["payload"] == payload
    assert len(envelope["payload_sha256"]) == 64

    index_path = job_dir / "artifact_index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index) == 1
    assert index[0]["artifact_type"] == "ingest.metadata"
