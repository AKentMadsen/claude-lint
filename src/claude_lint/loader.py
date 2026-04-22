"""Discover and parse a .claude/ tree."""
from __future__ import annotations

import json
from pathlib import Path

from claude_lint import frontmatter
from claude_lint.config import Config
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


def _iter_skill_files(root: Path, recursive: bool) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    if recursive:
        for p in sorted(root.rglob("SKILL.md")):
            files.append(p)
        for p in sorted(root.glob("*.md")):
            if p.is_file() and p.name != "SKILL.md":
                files.append(p)
        return files
    for child in sorted(root.iterdir()):
        if child.is_dir():
            skill_md = child / "SKILL.md"
            if skill_md.is_file():
                files.append(skill_md)
        elif child.is_file() and child.suffix == ".md":
            files.append(child)
    return files


def _is_ignored(path: Path, ignore_paths: list[str]) -> bool:
    s = str(path)
    return any(tok in s for tok in ignore_paths)


def load(claude_dir: Path, cfg: Config | None = None) -> ClaudeTree:
    """Load a single project root or .claude/ directory.

    When `cfg.skills_dirs` / `cfg.agents_dirs` are set, they override the
    default `.claude/skills` and `.claude/agents`. Paths are resolved relative
    to `claude_dir.parent` when `claude_dir` is itself `.claude`, else to
    `claude_dir` itself.
    """
    cfg = cfg or Config()
    tree = ClaudeTree(root=claude_dir)

    # Resolve project root — if we were handed a .claude/ dir, its parent is root.
    project_root = claude_dir.parent if claude_dir.name == ".claude" else claude_dir

    def _resolve(paths: list[str], default: Path) -> list[Path]:
        if not paths:
            return [default]
        return [project_root / p for p in paths]

    skill_roots = _resolve(cfg.skills_dirs, claude_dir / "skills")
    agent_roots = _resolve(cfg.agents_dirs, claude_dir / "agents")

    # skills
    skill_files: list[Path] = []
    for root in skill_roots:
        for p in _iter_skill_files(root, cfg.recursive_skills):
            if not _is_ignored(p, cfg.ignore_paths):
                skill_files.append(p)
    tree.skills = [_read(p) for p in skill_files]

    # agents — flat .md files per root
    agent_files: list[Path] = []
    for root in agent_roots:
        if root.exists():
            for p in sorted(root.glob("*.md")):
                if not _is_ignored(p, cfg.ignore_paths):
                    agent_files.append(p)
    tree.agents = [_read(p) for p in agent_files]

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


def find_claude_dirs(start: Path, cfg: Config | None = None) -> list[Path]:
    """Find directories to lint.

    Precedence:
    1. `start` is a .claude dir → lint that.
    2. `start/.claude` exists → lint that.
    3. `cfg` overrides skills/agents dirs → treat `start` as the project root.
    4. `start` has root-level `agents/` or `skill-library/` → treat `start` as root.
    5. Otherwise scan one level deep for `*/.claude`.
    """
    start = start.resolve()
    if start.name == ".claude" and start.is_dir():
        return [start]
    direct = start / ".claude"
    if direct.is_dir():
        # also include the project root when config overrides exist
        if cfg and (cfg.skills_dirs or cfg.agents_dirs):
            return [start]
        return [direct]
    if cfg and (cfg.skills_dirs or cfg.agents_dirs):
        return [start]
    # auto-detect a non-.claude skill/agent repo
    if start.is_dir() and (
        (start / "agents").is_dir() or (start / "skill-library").is_dir()
    ):
        return [start]
    found: list[Path] = []
    if start.is_dir():
        for child in start.iterdir():
            if child.is_dir():
                cand = child / ".claude"
                if cand.is_dir():
                    found.append(cand)
    return found
