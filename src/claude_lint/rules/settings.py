"""settings.json structural rules (non-security).

CL030  settings.json does not parse
CL031  unknown hook event name
CL032  hook command references missing script
CL033  'permissions.allow' references unknown tool prefix
"""
from __future__ import annotations

import shlex
from pathlib import Path

from claude_lint.config import Config
from claude_lint.known import KNOWN_HOOK_EVENTS, KNOWN_TOOLS
from claude_lint.models import ClaudeTree, Finding, Severity


def _check_hooks(settings_path: Path, data: dict) -> list[Finding]:
    out: list[Finding] = []
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return out
    for event, matchers in hooks.items():
        if event not in KNOWN_HOOK_EVENTS:
            out.append(
                Finding(
                    rule_id="CL031",
                    severity=Severity.ERROR,
                    message=f"unknown hook event '{event}'",
                    path=settings_path,
                )
            )
        if not isinstance(matchers, list):
            continue
        for m in matchers:
            for h in (m or {}).get("hooks", []) or []:
                cmd = (h or {}).get("command")
                if not isinstance(cmd, str) or not cmd.strip():
                    continue
                parts = shlex.split(cmd, posix=True)
                if not parts:
                    continue
                first = Path(parts[0].replace("$HOME", str(Path.home())))
                if first.is_absolute() and not first.exists():
                    out.append(
                        Finding(
                            rule_id="CL032",
                            severity=Severity.ERROR,
                            message=f"hook command references missing script '{first}'",
                            path=settings_path,
                        )
                    )
    return out


def _check_permissions(settings_path: Path, data: dict, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    perms = data.get("permissions") or {}
    allow = perms.get("allow") or []
    allowed_tools = KNOWN_TOOLS | cfg.extra_tools
    for entry in allow:
        if not isinstance(entry, str):
            continue
        bare = entry.strip()
        if bare.startswith("mcp__") or bare == "*":
            continue
        head = bare.split("(", 1)[0]
        if head not in allowed_tools:
            out.append(
                Finding(
                    rule_id="CL033",
                    severity=Severity.WARN,
                    message=f"permissions.allow references unknown tool '{bare}'",
                    path=settings_path,
                )
            )
    return out


def check(tree: ClaudeTree, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    for sp, data, err in tree.settings:
        if err:
            out.append(
                Finding(
                    rule_id="CL030",
                    severity=Severity.ERROR,
                    message=f"settings.json does not parse: {err}",
                    path=sp,
                )
            )
            continue
        if not isinstance(data, dict):
            continue
        out += _check_hooks(sp, data)
        out += _check_permissions(sp, data, cfg)
    return out
