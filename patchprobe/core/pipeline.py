from __future__ import annotations

from . import ingest, normalize, diff, rank, decompile, llm, validate, report
from .audit import append_audit_entry


def _job_dir_from_args(args) -> str | None:
    job = getattr(args, "job", None)
    if isinstance(job, str):
        return job
    out = getattr(args, "out", None)
    if isinstance(out, str):
        return out
    return None


def _run_stage(stage: str, fn, cfg: dict, args) -> None:
    job_dir = _job_dir_from_args(args)
    if job_dir:
        append_audit_entry(job_dir, stage, "start")
    try:
        fn(cfg, args)
        if job_dir:
            append_audit_entry(job_dir, stage, "success")
    except Exception as e:  # noqa: BLE001
        if job_dir:
            append_audit_entry(job_dir, stage, "error", {"error": str(e)})
        raise


def run_ingest(cfg: dict, args) -> None:
    _run_stage("ingest", ingest.run, cfg, args)


def run_diff(cfg: dict, args) -> None:
    _run_stage("diff", diff.run, cfg, args)


def run_normalize(cfg: dict, args) -> None:
    _run_stage("normalize", normalize.run, cfg, args)


def run_rank(cfg: dict, args) -> None:
    _run_stage("rank", rank.run, cfg, args)


def run_decompile(cfg: dict, args) -> None:
    _run_stage("decompile", decompile.run, cfg, args)


def run_analyze(cfg: dict, args) -> None:
    _run_stage("analyze", llm.run, cfg, args)


def run_validate(cfg: dict, args) -> None:
    _run_stage("validate", validate.run, cfg, args)


def run_report(cfg: dict, args) -> None:
    _run_stage("report", report.run, cfg, args)


def run_all(cfg: dict, args) -> None:
    run_ingest(cfg, args)
    if getattr(args, "job", None) is None:
        setattr(args, "job", args.out)
    run_normalize(cfg, args)
    run_diff(cfg, args)
    run_rank(cfg, args)
    run_decompile(cfg, args)
    run_analyze(cfg, args)
    run_validate(cfg, args)
    run_report(cfg, args)
