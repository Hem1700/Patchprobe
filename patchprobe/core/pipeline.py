from __future__ import annotations

from . import ingest, diff, rank, decompile, llm, validate, report


def run_ingest(cfg: dict, args) -> None:
    ingest.run(cfg, args)


def run_diff(cfg: dict, args) -> None:
    diff.run(cfg, args)


def run_rank(cfg: dict, args) -> None:
    rank.run(cfg, args)


def run_decompile(cfg: dict, args) -> None:
    decompile.run(cfg, args)


def run_analyze(cfg: dict, args) -> None:
    llm.run(cfg, args)


def run_validate(cfg: dict, args) -> None:
    validate.run(cfg, args)


def run_report(cfg: dict, args) -> None:
    report.run(cfg, args)


def run_all(cfg: dict, args) -> None:
    ingest.run(cfg, args)
    diff.run(cfg, args)
    rank.run(cfg, args)
    decompile.run(cfg, args)
    llm.run(cfg, args)
    validate.run(cfg, args)
    report.run(cfg, args)
