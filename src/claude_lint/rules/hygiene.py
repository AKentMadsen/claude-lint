"""Size and cleanliness rules.

CL020  MEMORY.md over line budget (default 200)
CL021  CLAUDE.md over line budget (default 500)
CL022  SKILL.md over line budget (default 800)
"""
from __future__ import annotations

from claude_lint.config import Config
from claude_lint.models import ClaudeTree, Finding, Severity


def check(tree: ClaudeTree, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    if tree.memory_index and tree.memory_index.line_count > cfg.max_memory_lines:
        out.append(
            Finding(
                rule_id="CL020",
                severity=Severity.WARN,
                message=(
                    f"MEMORY.md is {tree.memory_index.line_count} lines "
                    f"(max {cfg.max_memory_lines}) — lines past the cap get truncated"
                ),
                path=tree.memory_index.path,
            )
        )
    if tree.claude_md and tree.claude_md.line_count > cfg.max_claude_md_lines:
        out.append(
            Finding(
                rule_id="CL021",
                severity=Severity.WARN,
                message=(
                    f"CLAUDE.md is {tree.claude_md.line_count} lines "
                    f"(max {cfg.max_claude_md_lines}) — consider splitting"
                ),
                path=tree.claude_md.path,
            )
        )
    for s in tree.skills:
        if s.line_count > cfg.max_skill_lines:
            out.append(
                Finding(
                    rule_id="CL022",
                    severity=Severity.WARN,
                    message=(
                        f"skill is {s.line_count} lines "
                        f"(max {cfg.max_skill_lines}) — split or trim"
                    ),
                    path=s.path,
                )
            )
    return out
