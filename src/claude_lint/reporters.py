from __future__ import annotations

import json
import sys
from collections import Counter

from claude_lint.models import Finding, Severity

_COLORS = {
    Severity.ERROR: "\033[31m",  # red
    Severity.WARN: "\033[33m",   # yellow
    Severity.INFO: "\033[36m",   # cyan
}
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _color(use_color: bool, s: str, code: str) -> str:
    if not use_color:
        return s
    return f"{code}{s}{_RESET}"


def text_report(findings: list[Finding], root: str, stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    use_color = stream.isatty()
    if not findings:
        stream.write(
            _color(use_color, f"✓ {root}: no findings\n", "\033[32m")
        )
        return

    by_severity: Counter[Severity] = Counter(f.severity for f in findings)
    stream.write(f"\n{_BOLD if use_color else ''}{root}{_RESET if use_color else ''}\n")
    for f in sorted(findings, key=lambda x: (str(x.path), x.rule_id)):
        tag = _color(use_color, f.severity.value.upper().ljust(5), _COLORS[f.severity])
        loc = f.location()
        stream.write(f"  {tag} {f.rule_id}  {loc}\n         {f.message}\n")
    total = len(findings)
    summary = (
        f"\n{total} finding(s): "
        f"{by_severity[Severity.ERROR]} error, "
        f"{by_severity[Severity.WARN]} warn, "
        f"{by_severity[Severity.INFO]} info\n"
    )
    stream.write(summary)


def json_report(findings: list[Finding], root: str, stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    payload = {
        "root": root,
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "message": f.message,
                "path": str(f.path),
                "line": f.line,
            }
            for f in findings
        ],
    }
    json.dump(payload, stream, indent=2)
    stream.write("\n")
