from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .base import DiffBackend
from ...core.job import Job
from ...core.artifacts import write_artifact
from ...utils.subprocess import run_command

_NM_LINE = re.compile(r"^([0-9A-Fa-f]+)\s+([A-Za-z])\s+(.+)$")
_FUNC_TYPES = {"t", "T", "w", "W"}


@dataclass
class Symbol:
    address: int
    symbol_type: str
    name: str


def _stable_id(prefix: str, *parts: str) -> str:
    joined = "::".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(joined).hexdigest()[:16]}"


def _normalize_name(name: str) -> str:
    return name[1:] if name.startswith("_") else name


def _parse_nm_output(stdout: str) -> list[Symbol]:
    symbols: list[Symbol] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _NM_LINE.match(line)
        if not m:
            continue
        addr_hex, symbol_type, name = m.groups()
        if symbol_type not in _FUNC_TYPES:
            continue
        try:
            address = int(addr_hex, 16)
        except ValueError:
            continue
        symbols.append(Symbol(address=address, symbol_type=symbol_type, name=name))
    return symbols


def _read_symbols(binary_path: str) -> list[Symbol]:
    result = run_command(["nm", "-n", binary_path], timeout=60)
    if result.returncode != 0:
        return []
    return _parse_nm_output(result.stdout)


def _match_symbols(symbols_a: list[Symbol], symbols_b: list[Symbol], job: Job) -> tuple[list[dict], list[dict]]:
    by_name_a = {_normalize_name(s.name): s for s in symbols_a if _normalize_name(s.name)}
    by_name_b = {_normalize_name(s.name): s for s in symbols_b if _normalize_name(s.name)}
    matched_names = sorted(set(by_name_a) & set(by_name_b))
    function_pairs: list[dict] = []
    diff_results: list[dict] = []
    for name in matched_names:
        sym_a = by_name_a[name]
        sym_b = by_name_b[name]
        func_pair_id = _stable_id("fp", name)
        func_id_a = _stable_id("fa", job.binary_a.sha256, name, hex(sym_a.address))
        func_id_b = _stable_id("fb", job.binary_b.sha256, name, hex(sym_b.address))
        function_pairs.append(
            {
                "func_pair_id": func_pair_id,
                "func_id_a": func_id_a,
                "func_id_b": func_id_b,
                "match_score": 1.0,
                "status": "matched_by_name",
                "evidence": [
                    f"symbol_name={name}",
                    f"addr_a=0x{sym_a.address:x}",
                    f"addr_b=0x{sym_b.address:x}",
                ],
                "metadata": {
                    "source": "nm",
                    "symbol_type_a": sym_a.symbol_type,
                    "symbol_type_b": sym_b.symbol_type,
                },
            }
        )
        diff_results.append(
            {
                "func_pair_id": func_pair_id,
                "change_summary": {
                    "symbol_name": name,
                    "address_changed": sym_a.address != sym_b.address,
                    "source": "nm",
                },
                "severity_hint": 0.2 if sym_a.address != sym_b.address else 0.05,
            }
        )
    return function_pairs, diff_results


class DiaphoraBackend(DiffBackend):
    def run(self, job: Job, job_dir: str) -> None:
        out_dir = Path(job_dir) / "artifacts" / "diff"
        out_dir.mkdir(parents=True, exist_ok=True)
        symbols_a = _read_symbols(job.binary_a.path)
        symbols_b = _read_symbols(job.binary_b.path)
        function_pairs, diff_results = _match_symbols(symbols_a, symbols_b, job)
        (out_dir / "function_pairs.json").write_text(json.dumps(function_pairs, indent=2), encoding="utf-8")
        (out_dir / "diff_results.json").write_text(json.dumps(diff_results, indent=2), encoding="utf-8")
        inputs = {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        }
        write_artifact(
            out_dir / "function_pairs.artifact.json",
            "diff.function_pairs",
            inputs,
            function_pairs,
            payload_schema="function_pair.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
        write_artifact(
            out_dir / "diff_results.artifact.json",
            "diff.results",
            inputs,
            diff_results,
            payload_schema="diff_result.schema.json",
            payload_is_list=True,
            job_dir=Path(job_dir),
        )
