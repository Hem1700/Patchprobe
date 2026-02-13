from __future__ import annotations

import json
from pathlib import Path

from .base import DecompileBackend
from ...core.artifacts import write_artifact
from ...core.job import Job


def _load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _select_ranked_candidates(job_dir: Path, top_n: int | None) -> list[dict]:
    ranked_path = job_dir / "artifacts" / "rank" / "ranked_candidates.json"
    ranked = _load_json(ranked_path, default={})
    if not isinstance(ranked, dict):
        return []
    candidates = ranked.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    if top_n is not None:
        return [c for c in candidates if isinstance(c, dict)][:top_n]
    return [c for c in candidates if isinstance(c, dict)]


def _load_function_pairs(job_dir: Path) -> dict[str, dict]:
    pairs_path = job_dir / "artifacts" / "diff" / "function_pairs.json"
    pairs = _load_json(pairs_path, default=[])
    if not isinstance(pairs, list):
        return {}
    out: dict[str, dict] = {}
    for pair in pairs:
        if not isinstance(pair, dict):
            continue
        key = pair.get("func_pair_id")
        if isinstance(key, str):
            out[key] = pair
    return out


def _build_stub_pseudocode(symbol_name: str) -> str:
    return (
        f"int {symbol_name}(void) {{\n"
        f"  // Placeholder output until Ghidra headless integration is complete.\n"
        f"  return 0;\n"
        f"}}\n"
    )


class GhidraHeadlessBackend(DecompileBackend):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        out_dir = Path(job_dir) / "artifacts" / "decompile"
        out_dir.mkdir(parents=True, exist_ok=True)

        job_path = Path(job_dir)
        ranked = _select_ranked_candidates(job_path, top_n=top_n)
        by_pair = _load_function_pairs(job_path)
        artifacts: list[dict] = []

        for candidate in ranked:
            func_pair_id = candidate.get("func_pair_id")
            if not isinstance(func_pair_id, str):
                continue
            pair = by_pair.get(func_pair_id, {})
            func_id_a = pair.get("func_id_a")
            func_id_b = pair.get("func_id_b")
            symbol_name = "unknown_function"
            evidence = pair.get("evidence", [])
            if isinstance(evidence, list):
                for item in evidence:
                    if isinstance(item, str) and item.startswith("symbol_name="):
                        symbol_name = item.split("=", 1)[1] or symbol_name
                        break

            for side, func_id, binary_sha in (
                ("A", func_id_a, job.binary_a.sha256),
                ("B", func_id_b, job.binary_b.sha256),
            ):
                if not isinstance(func_id, str):
                    continue
                item_dir = out_dir / func_id
                item_dir.mkdir(parents=True, exist_ok=True)
                pseudocode = _build_stub_pseudocode(symbol_name)
                pseudocode_path = item_dir / "pseudocode.txt"
                pseudocode_path.write_text(pseudocode, encoding="utf-8")
                meta = {
                    "func_id": func_id,
                    "func_pair_id": func_pair_id,
                    "binary_side": side,
                    "binary_sha": binary_sha,
                    "prototype": f"int {symbol_name}(void)",
                    "pseudocode": pseudocode,
                    "callers": [],
                    "callees": [],
                    "strings": [],
                    "status": "placeholder_success",
                    "error": None,
                    "timeout_seconds": timeout,
                    "backend": "ghidra_headless_stub",
                }
                (item_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                artifacts.append(meta)

        (out_dir / "decompile_artifacts.json").write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
        write_artifact(
            out_dir / "decompile_artifacts.artifact.json",
            "decompile.artifacts",
            {
                "binary_a_sha256": job.binary_a.sha256,
                "binary_b_sha256": job.binary_b.sha256,
                "upstream_artifact_hashes": [],
            },
            artifacts,
            payload_schema="decompile_artifact.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
