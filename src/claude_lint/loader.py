"""Discover and parse a .claude/ tree."""
from __future__ import annotations

import json
from pathlib import Path

from claude_lint import frontmatter
from claude_lint.models import ClaudeTree, ParsedFile


def _read(path: Path) -> ParsedFile:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body, err, start = frontmatter.parse(text)
    return ParsedFile(
        path=path,
        frontmatter=fm,
        body=body,
        frontmatter_start_line=start,
        frontmatter_error=err,
        line_count=text.count("\n") + (0 if text.endswith("\n") else 1),
    )


def _iter_skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for child in sorted(root.iterdir()):
        if child.is_dir():
            skill_md = child / "SKILL.md"
            if skill_md.is_file():
                files.append(skill_md)
        elif child.is_file() and child.suffix == ".md":
            files.append(child)
    return files


def load(claude_dir: Path) -> ClaudeTree:
    """Load a single .claude/ directory (not nested)."""
    tree = ClaudeTree(root=claude_dir)

    # skills — each skill is a directory containing SKILL.md, or a bare .md
    tree.skills = [_read(p) for p in _iter_skill_files(claude_dir / "skills")]

    # agents — flat .md files
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        tree.agents = [_read(p) for p in sorted(agents_dir.glob("*.md"))]

    # commands — flat .md files
    cmds_dir = claude_dir / "commands"
    if cmds_dir.exists():
        tree.commands = [_read(p) for p in sorted(cmds_dir.glob("*.md"))]

    # CLAUDE.md at root or parent (parent is the actual project root)
    for candidate in (claude_dir.parent / "CLAUDE.md", claude_dir / "CLAUDE.md"):
        if candidate.is_file():
            tree.claude_md = _read(candidate)
            break

    # memory — optional subdir with MEMORY.md index
    mem_dir = claude_dir / "memory"
    if not mem_dir.exists():
        # also accept projects/*/memory pattern for user-global trees
        projects_dir = claude_dir / "projects"
        if projects_dir.exists():
            for proj in projects_dir.iterdir():
                p_mem = proj / "memory"
                if p_mem.exists():
                    mem_dir = p_mem
                    break
    if mem_dir.exists():
        mem_index = mem_dir / "MEMORY.md"
        if mem_index.is_file():
            tree.memory_index = _read(mem_index)
        tree.memory_files = [
            _read(p)
            for p in sorted(mem_dir.glob("*.md"))
            if p.name != "MEMORY.md"
        ]

    # settings — settings.json / settings.local.json at claude_dir root
    for name in ("settings.json", "settings.local.json"):
        sp = claude_dir / name
        if sp.is_file():
            try:
                tree.settings.append((sp, json.loads(sp.read_text(encoding="utf-8")), None))
            except json.JSONDecodeError as e:
                tree.settings.append((sp, None, str(e)))

    hooks = claude_dir / "hooks"
    tree.hooks_dir = hooks if hooks.exists() else None

    return tree


def find_claude_dirs(start: Path) -> list[Path]:
    """Find .claude directories to lint.

    If `start` is a .claude dir, lint that.
    If `start` contains a .claude dir, lint that.
    Otherwise, search one level deep (useful when pointed at a parent workspace).
    """
    start = start.resolve()
    if start.name == ".claude" and start.is_dir():
        return [start]
    direct = start / ".claude"
    if direct.is_dir():
        return [direct]
    found: list[Path] = []
    if start.is_dir():
        for child in start.iterdir():
            if child.is_dir():
                cand = child / ".claude"
                if cand.is_dir():
                    found.append(cand)
    return found
