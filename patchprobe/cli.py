from __future__ import annotations

import argparse
import sys

from .config import load_config
from .logging import configure_logging
from .errors import PatchdiffError
from .core import pipeline


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="patchdiff", description="LLM-assisted binary patch diffing (defender-focused)")
    p.add_argument("--config", help="Path to config file", default=None)
    p.add_argument("--log-level", help="Log level", default=None)

    sub = p.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest binaries and create job")
    ingest.add_argument("--a", required=True)
    ingest.add_argument("--b", required=True)
    ingest.add_argument("--tag", default=None)
    ingest.add_argument("--out", required=True)

    diff = sub.add_parser("diff", help="Run diff backend")
    diff.add_argument("--job", required=True)
    diff.add_argument("--backend", default=None)

    rank = sub.add_parser("rank", help="Rank candidate function pairs")
    rank.add_argument("--job", required=True)
    rank.add_argument("--top", type=int, default=None)

    decompile = sub.add_parser("decompile", help="Decompile top candidates")
    decompile.add_argument("--job", required=True)
    decompile.add_argument("--top", type=int, default=None)
    decompile.add_argument("--timeout", type=int, default=90)

    analyze = sub.add_parser("analyze", help="Run LLM analysis")
    analyze.add_argument("--job", required=True)
    analyze.add_argument("--provider", default=None)
    analyze.add_argument("--model", default=None)
    analyze.add_argument("--max-rounds", type=int, default=None)

    validate = sub.add_parser("validate", help="Validate LLM output")
    validate.add_argument("--job", required=True)

    report = sub.add_parser("report", help="Generate report")
    report.add_argument("--job", required=True)
    report.add_argument("--format", default=None)

    run = sub.add_parser("run", help="End-to-end pipeline")
    run.add_argument("--a", required=True)
    run.add_argument("--b", required=True)
    run.add_argument("--tag", default=None)
    run.add_argument("--out", required=True)
    run.add_argument("--backend", default=None)
    run.add_argument("--top", type=int, default=None)
    run.add_argument("--timeout", type=int, default=90)
    run.add_argument("--provider", default=None)
    run.add_argument("--model", default=None)
    run.add_argument("--max-rounds", type=int, default=None)
    run.add_argument("--format", default=None)

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    cfg = load_config(args.config)
    configure_logging(level=args.log_level or "INFO")

    try:
        if args.command == "ingest":
            pipeline.run_ingest(cfg, args)
        elif args.command == "diff":
            pipeline.run_diff(cfg, args)
        elif args.command == "rank":
            pipeline.run_rank(cfg, args)
        elif args.command == "decompile":
            pipeline.run_decompile(cfg, args)
        elif args.command == "analyze":
            pipeline.run_analyze(cfg, args)
        elif args.command == "validate":
            pipeline.run_validate(cfg, args)
        elif args.command == "report":
            pipeline.run_report(cfg, args)
        elif args.command == "run":
            pipeline.run_all(cfg, args)
        else:
            parser.error("Unknown command")
    except PatchdiffError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
