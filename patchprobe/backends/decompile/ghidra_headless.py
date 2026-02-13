from __future__ import annotations

import json
import os
from pathlib import Path

from .base import DecompileBackend
from ...core.artifacts import write_artifact
from ...core.job import Job
from ...utils.subprocess import run_command

DEFAULT_RUNNER = Path(__file__).resolve().parents[3] / "scripts" / "run_ghidra_headless.sh"
DEFAULT_POST_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "ghidra_decompile.py"


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


def _resolve_runner(job: Job) -> str | None:
    cfg_runner = (
        job.config.get("decompile", {}).get("ghidra_runner")
        if isinstance(job.config, dict)
        else None
    )
    runner = cfg_runner or os.environ.get("PATCHDIFF_GHIDRA_RUNNER") or str(DEFAULT_RUNNER)
    path = Path(runner)
    if path.exists():
        return str(path)
    return None


def _attempt_ghidra_decompile(
    runner: str,
    job_dir: Path,
    binary_path: str,
    symbol_name: str,
    item_dir: Path,
    timeout: int,
) -> tuple[str, str | None, str, str | None]:
    output_json = item_dir / "ghidra_output.json"
    output_txt = item_dir / "pseudocode.txt"
    project_dir = job_dir / "artifacts" / "decompile" / "ghidra_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    result = run_command(
        [
            runner,
            str(project_dir),
            binary_path,
            str(DEFAULT_POST_SCRIPT),
            symbol_name,
            str(output_json),
            str(output_txt),
            str(timeout),
        ],
        timeout=timeout,
    )
    if result.returncode != 0:
        return (
            _build_stub_pseudocode(symbol_name),
            f"int {symbol_name}(void)",
            "ghidra_headless_failed",
            (result.stderr or result.stdout or f"exit={result.returncode}").strip(),
        )
    if not output_txt.exists():
        return (
            _build_stub_pseudocode(symbol_name),
            f"int {symbol_name}(void)",
            "ghidra_headless_failed",
            "runner succeeded but pseudocode output file missing",
        )
    pseudocode = output_txt.read_text(encoding="utf-8", errors="replace")
    prototype: str | None = None
    if output_json.exists():
        try:
            parsed = json.loads(output_json.read_text(encoding="utf-8"))
            p = parsed.get("prototype")
            if isinstance(p, str):
                prototype = p
        except Exception:  # noqa: BLE001
            prototype = None
    return pseudocode, prototype or f"int {symbol_name}(void)", "ghidra_headless_success", None


class GhidraHeadlessBackend(DecompileBackend):
    def run(self, job: Job, job_dir: str, top_n: int | None, timeout: int) -> None:
        out_dir = Path(job_dir) / "artifacts" / "decompile"
        out_dir.mkdir(parents=True, exist_ok=True)
        runner = _resolve_runner(job)

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
                if runner:
                    pseudocode, prototype, status, error = _attempt_ghidra_decompile(
                        runner=runner,
                        job_dir=job_path,
                        binary_path=job.binary_a.path if side == "A" else job.binary_b.path,
                        symbol_name=symbol_name,
                        item_dir=item_dir,
                        timeout=timeout,
                    )
                    backend_name = "ghidra_headless"
                else:
                    pseudocode = _build_stub_pseudocode(symbol_name)
                    prototype = f"int {symbol_name}(void)"
                    status = "ghidra_headless_unavailable"
                    error = "runner not found"
                    backend_name = "ghidra_headless_stub"
                pseudocode_path = item_dir / "pseudocode.txt"
                pseudocode_path.write_text(pseudocode, encoding="utf-8")
                meta = {
                    "func_id": func_id,
                    "func_pair_id": func_pair_id,
                    "binary_side": side,
                    "binary_sha": binary_sha,
                    "prototype": prototype,
                    "pseudocode": pseudocode,
                    "callers": [],
                    "callees": [],
                    "strings": [],
                    "status": status,
                    "error": error,
                    "timeout_seconds": timeout,
                    "backend": backend_name,
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
