from __future__ import annotations

import argparse
import json
import os
import sys

from .config import load_config, resolve_config_path, validate_config
from .constants import DEFAULT_LOG_LEVEL, ENV_LOG_LEVEL
from .logging import configure_logging
from .errors import CliArgumentError, PatchdiffError
from .core import pipeline


class PatchdiffArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def _build_parser() -> argparse.ArgumentParser:
    examples = (
        "Examples:\n"
        "  patchdiff ingest --a ./before.bin --b ./after.bin --out ./jobs/job_001\n"
        "  patchdiff diff --job ./jobs/job_001 --backend ghidra\n"
        "  patchdiff rank --job ./jobs/job_001 --top 30\n"
        "  patchdiff decompile --job ./jobs/job_001 --top 30\n"
        "  patchdiff analyze --job ./jobs/job_001 --provider local --model llama3\n"
        "  patchdiff validate --job ./jobs/job_001\n"
        "  patchdiff report --job ./jobs/job_001 --format markdown\n"
        "  patchdiff run --a ./before.bin --b ./after.bin --out ./jobs/job_001 --top 30\n"
    )
    p = PatchdiffArgumentParser(
        prog="patchdiff",
        description="LLM-assisted binary patch diffing (defender-focused)",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--config", help="Path to config file", default=None)
    p.add_argument("--log-level", help="Log level", default=None)

    sub = p.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser(
        "ingest",
        help="Ingest binaries and create job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff ingest --a ./before.bin --b ./after.bin --out ./jobs/job_001",
    )
    ingest.add_argument("--a", required=True)
    ingest.add_argument("--b", required=True)
    ingest.add_argument("--tag", default=None)
    ingest.add_argument("--out", required=True)

    diff = sub.add_parser(
        "diff",
        help="Run diff backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff diff --job ./jobs/job_001 --backend ghidra",
    )
    diff.add_argument("--job", required=True)
    diff.add_argument("--backend", default=None)

    rank = sub.add_parser(
        "rank",
        help="Rank candidate function pairs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff rank --job ./jobs/job_001 --top 30",
    )
    rank.add_argument("--job", required=True)
    rank.add_argument("--top", type=int, default=None)

    decompile = sub.add_parser(
        "decompile",
        help="Decompile top candidates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff decompile --job ./jobs/job_001 --top 30",
    )
    decompile.add_argument("--job", required=True)
    decompile.add_argument("--top", type=int, default=None)
    decompile.add_argument("--timeout", type=int, default=90)

    analyze = sub.add_parser(
        "analyze",
        help="Run LLM analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff analyze --job ./jobs/job_001 --provider local --model llama3",
    )
    analyze.add_argument("--job", required=True)
    analyze.add_argument("--provider", default=None)
    analyze.add_argument("--model", default=None)
    analyze.add_argument("--max-rounds", type=int, default=None)

    validate = sub.add_parser(
        "validate",
        help="Validate LLM output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff validate --job ./jobs/job_001",
    )
    validate.add_argument("--job", required=True)

    report = sub.add_parser(
        "report",
        help="Generate report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff report --job ./jobs/job_001 --format markdown",
    )
    report.add_argument("--job", required=True)
    report.add_argument("--format", default=None)

    run = sub.add_parser(
        "run",
        help="End-to-end pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  patchdiff run --a ./before.bin --b ./after.bin --out ./jobs/job_001 --top 30",
    )
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
    try:
        args = parser.parse_args()
        cfg_path = resolve_config_path(args.config)
        cfg = load_config(str(cfg_path))
        validate_config(cfg)
        log_level = args.log_level or os.environ.get(ENV_LOG_LEVEL) or DEFAULT_LOG_LEVEL
        configure_logging(level=log_level)

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
        if e.details:
            print(f"details: {json.dumps(e.details, indent=2)}", file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
