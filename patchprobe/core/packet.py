from __future__ import annotations

from dataclasses import asdict

from .job import Job


def build_packet(job: Job, func_id: str, diff: dict, decompile_a: dict, decompile_b: dict) -> dict:
    return {
        "job_id": job.job_id,
        "binary_a": asdict(job.binary_a),
        "binary_b": asdict(job.binary_b),
        "function": {
            "func_id": func_id,
            "name_a": decompile_a.get("name"),
            "name_b": decompile_b.get("name"),
            "prototype_a": decompile_a.get("prototype"),
            "prototype_b": decompile_b.get("prototype"),
            "callers_a": decompile_a.get("callers", []),
            "callers_b": decompile_b.get("callers", []),
        },
        "diff": diff,
        "questions": [
            "What is the most likely bug class fixed here?",
            "What evidence supports that?",
            "What are the preconditions for reaching this code?",
            "List defensive validation tests.",
        ],
        "required_output_schema": "specs/schemas/llm_output.schema.json",
    }
