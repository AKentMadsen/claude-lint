"""Frontmatter schema rules.

CL001  frontmatter parse error
CL002  skill/agent/command missing required field
CL003  description too short
CL004  description too long
CL005  name mismatches filename/dirname
CL006  tools list references unknown tool
CL007  model id is stale or unrecognized
"""
from __future__ import annotations

from claude_lint.config import Config
from claude_lint.known import (
    CURRENT_MODEL_PREFIXES,
    KNOWN_TOOLS,
    STALE_MODEL_PREFIXES,
)
from claude_lint.models import ClaudeTree, Finding, ParsedFile, Severity


def _required_fields(kind: str) -> list[str]:
    if kind == "skill":
        return ["description"]
    if kind == "agent":
        return ["description"]
    if kind == "command":
        return []
    return []


def _expected_name(kind: str, f: ParsedFile) -> str:
    if kind == "skill" and f.path.name == "SKILL.md":
        return f.path.parent.name
    return f.path.stem


def _check_file(kind: str, f: ParsedFile, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    if f.frontmatter_error:
        out.append(
            Finding(
                rule_id="CL001",
                severity=Severity.ERROR,
                message=f"{kind} frontmatter parse error: {f.frontmatter_error}",
                path=f.path,
                line=f.frontmatter_start_line,
            )
        )
        return out
    if f.frontmatter is None:
        if kind in ("skill", "agent"):
            out.append(
                Finding(
                    rule_id="CL002",
                    severity=Severity.ERROR,
                    message=f"{kind} is missing YAML frontmatter",
                    path=f.path,
                    line=1,
                )
            )
        return out

    fm = f.frontmatter
    for field_name in _required_fields(kind):
        if not fm.get(field_name):
            out.append(
                Finding(
                    rule_id="CL002",
                    severity=Severity.ERROR,
                    message=f"{kind} missing required field '{field_name}'",
                    path=f.path,
                    line=f.frontmatter_start_line,
                )
            )

    desc = fm.get("description")
    if isinstance(desc, str) and desc:
        if len(desc) < cfg.min_description_chars:
            out.append(
                Finding(
                    rule_id="CL003",
                    severity=Severity.WARN,
                    message=(
                        f"{kind} description is short "
                        f"({len(desc)} chars, min {cfg.min_description_chars}) — "
                        "autoload matching suffers"
                    ),
                    path=f.path,
                    line=f.frontmatter_start_line,
                )
            )
        if len(desc) > cfg.max_description_chars:
            out.append(
                Finding(
                    rule_id="CL004",
                    severity=Severity.WARN,
                    message=(
                        f"{kind} description is long "
                        f"({len(desc)} chars, max {cfg.max_description_chars}) — "
                        "inflates prompt tokens"
                    ),
                    path=f.path,
                    line=f.frontmatter_start_line,
                )
            )

    name = fm.get("name")
    expected = _expected_name(kind, f)
    if isinstance(name, str) and name and name != expected:
        out.append(
            Finding(
                rule_id="CL005",
                severity=Severity.WARN,
                message=f"{kind} name '{name}' does not match expected '{expected}'",
                path=f.path,
                line=f.frontmatter_start_line,
            )
        )

    tools = fm.get("tools")
    if isinstance(tools, list):
        allowed = KNOWN_TOOLS | cfg.extra_tools
        for t in tools:
            if not isinstance(t, str):
                continue
            bare = t.strip()
            # MCP tools like mcp__server__tool are always accepted.
            if bare.startswith("mcp__"):
                continue
            # Tool with parens like Bash(npm:*) — check the prefix.
            head = bare.split("(", 1)[0]
            if head not in allowed:
                out.append(
                    Finding(
                        rule_id="CL006",
                        severity=Severity.ERROR,
                        message=f"{kind} references unknown tool '{bare}'",
                        path=f.path,
                        line=f.frontmatter_start_line,
                    )
                )

    model = fm.get("model")
    if isinstance(model, str) and model:
        low = model.strip()
        if any(low.startswith(p) for p in STALE_MODEL_PREFIXES):
            out.append(
                Finding(
                    rule_id="CL007",
                    severity=Severity.WARN,
                    message=f"{kind} uses stale model '{model}' — upgrade to a claude-4.x id",
                    path=f.path,
                    line=f.frontmatter_start_line,
                )
            )
        elif not any(low.startswith(p) for p in CURRENT_MODEL_PREFIXES):
            out.append(
                Finding(
                    rule_id="CL007",
                    severity=Severity.INFO,
                    message=f"{kind} model '{model}' not recognized — double-check id",
                    path=f.path,
                    line=f.frontmatter_start_line,
                )
            )

    return out


def check(tree: ClaudeTree, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    for f in tree.skills:
        out += _check_file("skill", f, cfg)
    for f in tree.agents:
        out += _check_file("agent", f, cfg)
    for f in tree.commands:
        out += _check_file("command", f, cfg)
    return out
