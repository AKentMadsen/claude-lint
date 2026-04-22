"""Cross-reference integrity.

CL010  MEMORY.md entry points to a missing file
CL011  memory file exists but not indexed in MEMORY.md (orphan)
CL012  duplicate skill/agent names across global + project scope (within same tree)
"""
from __future__ import annotations

import re
from pathlib import Path

from claude_lint.config import Config
from claude_lint.models import ClaudeTree, Finding, Severity


_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _memory_links(index_body: str) -> list[str]:
    hits = _LINK_RE.findall(index_body)
    return [h.strip() for h in hits if not h.startswith(("http://", "https://"))]


def _check_memory(tree: ClaudeTree) -> list[Finding]:
    out: list[Finding] = []
    if tree.memory_index is None:
        return out

    mem_dir = tree.memory_index.path.parent
    linked = set(_memory_links(tree.memory_index.body))
    for link in linked:
        target = (mem_dir / link).resolve()
        if not target.exists():
            out.append(
                Finding(
                    rule_id="CL010",
                    severity=Severity.ERROR,
                    message=f"MEMORY.md references missing file '{link}'",
                    path=tree.memory_index.path,
                )
            )

    indexed_names = {Path(link).name for link in linked}
    for mf in tree.memory_files:
        if mf.path.name not in indexed_names:
            out.append(
                Finding(
                    rule_id="CL011",
                    severity=Severity.WARN,
                    message=f"memory file '{mf.path.name}' is not indexed in MEMORY.md",
                    path=mf.path,
                )
            )
    return out


def _check_duplicates(tree: ClaudeTree) -> list[Finding]:
    out: list[Finding] = []
    seen: dict[str, Path] = {}
    for f in tree.skills:
        name = (
            f.path.parent.name
            if f.path.name == "SKILL.md"
            else f.path.stem
        )
        if name in seen:
            out.append(
                Finding(
                    rule_id="CL012",
                    severity=Severity.WARN,
                    message=f"duplicate skill name '{name}' (also at {seen[name]})",
                    path=f.path,
                )
            )
        else:
            seen[name] = f.path
    agent_seen: dict[str, Path] = {}
    for f in tree.agents:
        name = f.path.stem
        if name in agent_seen:
            out.append(
                Finding(
                    rule_id="CL012",
                    severity=Severity.WARN,
                    message=f"duplicate agent name '{name}' (also at {agent_seen[name]})",
                    path=f.path,
                )
            )
        else:
            agent_seen[name] = f.path
    return out


def check(tree: ClaudeTree, cfg: Config) -> list[Finding]:
    return _check_memory(tree) + _check_duplicates(tree)
