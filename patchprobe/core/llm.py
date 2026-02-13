from __future__ import annotations

import json
from pathlib import Path

from .artifacts import write_artifact
from .packet import build_packet
from .job import load_job
from ..backends.llm import get_provider
from ..utils.time import now_iso


def _load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _guess_bug_class(packet: dict) -> tuple[str, list[str]]:
    text = " ".join(
        [
            str(packet.get("diff", {}).get("change_summary", "")),
            str(packet.get("code", {}).get("pseudocode_a", "")),
            str(packet.get("code", {}).get("pseudocode_b", "")),
        ]
    ).lower()
    notes: list[str] = []
    if any(k in text for k in ("bounds", "length", "range", "index")):
        notes.append("Detected bounds-related keywords in diff/pseudocode.")
        return "bounds-check-hardening", notes
    if "null" in text:
        notes.append("Detected null-handling keywords in diff/pseudocode.")
        return "null-check-hardening", notes
    return "logic-fix", notes


def _build_analysis_from_packet(packet: dict, provider_name: str, model: str, provider_result: dict) -> dict:
    bug_class, notes = _guess_bug_class(packet)
    change_summary = packet.get("diff", {}).get("change_summary", {})
    evidence = [
        {
            "type": "diff_summary",
            "snippet": json.dumps(change_summary, sort_keys=True),
            "location": "diff.change_summary",
        }
    ]
    return {
        "func_pair_id": packet.get("function", {}).get("func_pair_id"),
        "bug_class": bug_class,
        "confidence": 0.35,
        "evidence": evidence,
        "reachability_notes": notes,
        "recommended_validation": [
            "Add regression test for matched function path.",
            "Add negative-path input validation test.",
        ],
        "safety": {"no_exploit_steps": True},
        "provider": provider_name,
        "model": model,
        "provider_result": provider_result,
    }


def run(cfg: dict, args) -> None:
    job = load_job(args.job)
    provider_name = args.provider or cfg.get("llm", {}).get("provider", "local")
    model = args.model or cfg.get("llm", {}).get("model", "llama3")
    max_rounds = args.max_rounds or cfg.get("llm", {}).get("max_rounds", 1)

    provider = get_provider(provider_name, model=model, max_rounds=max_rounds)

    out_dir = Path(args.job) / "artifacts" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    ranked = _load_json(Path(args.job) / "artifacts" / "rank" / "ranked_candidates.json", default={})
    candidates = ranked.get("candidates", []) if isinstance(ranked, dict) else []
    if not isinstance(candidates, list):
        candidates = []
    function_pairs = _load_json(Path(args.job) / "artifacts" / "diff" / "function_pairs.json", default=[])
    if not isinstance(function_pairs, list):
        function_pairs = []
    diff_results = _load_json(Path(args.job) / "artifacts" / "diff" / "diff_results.json", default=[])
    if not isinstance(diff_results, list):
        diff_results = []
    decompile_items = _load_json(Path(args.job) / "artifacts" / "decompile" / "decompile_artifacts.json", default=[])
    if not isinstance(decompile_items, list):
        decompile_items = []

    pairs_by_id = {p.get("func_pair_id"): p for p in function_pairs if isinstance(p, dict)}
    diffs_by_id = {d.get("func_pair_id"): d for d in diff_results if isinstance(d, dict)}
    decompile_by_func_id = {d.get("func_id"): d for d in decompile_items if isinstance(d, dict)}
    analyses: list[dict] = []
    packets: list[dict] = []
    round_outputs: list[dict] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        func_pair_id = candidate.get("func_pair_id")
        if not isinstance(func_pair_id, str):
            continue
        pair = pairs_by_id.get(func_pair_id, {})
        func_id_a = pair.get("func_id_a")
        func_id_b = pair.get("func_id_b")
        if not isinstance(func_id_a, str) or not isinstance(func_id_b, str):
            continue
        decomp_a = decompile_by_func_id.get(func_id_a, {})
        decomp_b = decompile_by_func_id.get(func_id_b, {})
        if not isinstance(decomp_a, dict) or not isinstance(decomp_b, dict):
            continue
        diff = diffs_by_id.get(func_pair_id, {"func_pair_id": func_pair_id, "change_summary": {}, "severity_hint": 0.0})
        packet = build_packet(job, func_pair_id, diff, decomp_a, decomp_b)
        packets.append(packet)
        latest_provider_result: dict = {}
        round_results: list[dict] = []
        for round_idx in range(1, max_rounds + 1):
            round_packet = {
                **packet,
                "analysis_round": round_idx,
                "analysis_max_rounds": max_rounds,
            }
            provider_result = provider.analyze(round_packet)
            if not isinstance(provider_result, dict):
                provider_result = {"status": "invalid_provider_output", "value": str(provider_result)}
            round_result = {
                "func_pair_id": func_pair_id,
                "round": round_idx,
                "provider_result": provider_result,
            }
            round_results.append(round_result)
            round_outputs.append(round_result)
            latest_provider_result = provider_result
        analysis = _build_analysis_from_packet(packet, provider_name, model, latest_provider_result)
        analysis["rounds"] = round_results
        analysis["round_count"] = len(round_results)
        analyses.append(analysis)

    output = {
        "job_id": job.job_id,
        "created_at": now_iso(),
        "max_rounds": max_rounds,
        "analysis": analyses,
    }
    (out_dir / "packets.json").write_text(json.dumps(packets, indent=2), encoding="utf-8")
    (out_dir / "round_outputs.json").write_text(json.dumps(round_outputs, indent=2), encoding="utf-8")
    (out_dir / "llm.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    write_artifact(
        out_dir / "llm.artifact.json",
        "analysis.llm",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        output,
        job_dir=Path(args.job),
    )
    schema_only = []
    for item in analyses:
        schema_only.append(
            {
                "bug_class": item["bug_class"],
                "confidence": item["confidence"],
                "evidence": item["evidence"],
                "reachability_notes": item["reachability_notes"],
                "recommended_validation": item["recommended_validation"],
                "safety": item["safety"],
            }
        )
    write_artifact(
        out_dir / "llm_outputs.artifact.json",
        "analysis.outputs",
        {
            "binary_a_sha256": job.binary_a.sha256,
            "binary_b_sha256": job.binary_b.sha256,
            "upstream_artifact_hashes": [],
        },
        schema_only,
        payload_schema="llm_output.schema.json",
        payload_is_list=True,
        job_dir=Path(args.job),
    )
