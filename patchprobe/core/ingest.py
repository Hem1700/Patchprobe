from __future__ import annotations

import json
from pathlib import Path

from ..errors import FileNotFoundErrorPatch, IngestError
from ..utils.hashing import sha256_file
from ..utils.filetype import detect_filetype_and_arch
from ..utils.time import now_iso
from .job import BinaryInfo, create_job


def _write_metadata(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run(cfg: dict, args) -> None:
    a_path = Path(args.a)
    b_path = Path(args.b)
    if not a_path.exists():
        raise FileNotFoundErrorPatch(f"binary A not found: {a_path}")
    if not b_path.exists():
        raise FileNotFoundErrorPatch(f"binary B not found: {b_path}")

    try:
        a_sha = sha256_file(a_path)
        b_sha = sha256_file(b_path)
        a_type, a_arch = detect_filetype_and_arch(a_path)
        b_type, b_arch = detect_filetype_and_arch(b_path)
    except Exception as e:
        raise IngestError(f"ingest failed: {e}")

    binary_a = BinaryInfo(path=str(a_path), sha256=a_sha, file_type=a_type, arch=a_arch)
    binary_b = BinaryInfo(path=str(b_path), sha256=b_sha, file_type=b_type, arch=b_arch)

    job = create_job(args.out, args.tag, binary_a, binary_b, cfg)

    ingest_dir = Path(args.out) / "artifacts" / "ingest"
    _write_metadata(ingest_dir / "metadata_a.json", {
        "binary": "A",
        "path": str(a_path),
        "sha256": a_sha,
        "file_type": a_type,
        "arch": a_arch,
        "created_at": now_iso(),
    })
    _write_metadata(ingest_dir / "metadata_b.json", {
        "binary": "B",
        "path": str(b_path),
        "sha256": b_sha,
        "file_type": b_type,
        "arch": b_arch,
        "created_at": now_iso(),
    })
