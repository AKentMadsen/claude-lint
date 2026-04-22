from __future__ import annotations

import argparse
import sys
from pathlib import Path

from claude_lint import __version__, config, loader, reporters, rules
from claude_lint.models import Severity


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claude-lint",
        description="Structural linter for .claude/ directories.",
    )
    p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root, a .claude directory, or a workspace parent to scan",
    )
    p.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    p.add_argument(
        "--min-severity",
        choices=("error", "warn", "info"),
        default="info",
    )
    p.add_argument(
        "--fail-on",
        choices=("error", "warn", "info", "none"),
        default="error",
        help="exit non-zero when any finding at this severity is present",
    )
    p.add_argument("--version", action="version", version=f"claude-lint {__version__}")
    return p


_SEV_ORDER = {Severity.INFO: 0, Severity.WARN: 1, Severity.ERROR: 2}


def _filter_min(findings, min_sev: str):
    floor = _SEV_ORDER[Severity(min_sev)]
    return [f for f in findings if _SEV_ORDER[f.severity] >= floor]


def _should_fail(findings, fail_on: str) -> bool:
    if fail_on == "none":
        return False
    floor = _SEV_ORDER[Severity(fail_on)]
    return any(_SEV_ORDER[f.severity] >= floor for f in findings)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = Path(args.path).resolve()
    if not start.exists():
        print(f"claude-lint: path does not exist: {start}", file=sys.stderr)
        return 2

    dirs = loader.find_claude_dirs(start)
    if not dirs:
        print(f"claude-lint: no .claude directory found under {start}", file=sys.stderr)
        return 2

    cfg = config.load(start)
    all_findings = []
    for cdir in dirs:
        tree = loader.load(cdir)
        findings = rules.run_all(tree, cfg)
        findings = _filter_min(findings, args.min_severity)
        all_findings.extend(findings)
        if args.format == "text":
            reporters.text_report(findings, str(cdir))
    if args.format == "json":
        reporters.json_report(all_findings, str(start))

    return 1 if _should_fail(all_findings, args.fail_on) else 0
