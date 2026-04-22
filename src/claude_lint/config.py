from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULTS = {
    "max_memory_lines": 200,
    "max_claude_md_lines": 500,
    "max_skill_lines": 800,
    "min_description_chars": 20,
    "max_description_chars": 400,
    "disabled_rules": [],
    "extra_tools": [],
}


@dataclass
class Config:
    max_memory_lines: int = 200
    max_claude_md_lines: int = 500
    max_skill_lines: int = 800
    min_description_chars: int = 20
    max_description_chars: int = 400
    disabled_rules: set[str] = field(default_factory=set)
    extra_tools: set[str] = field(default_factory=set)


def load(start: Path) -> Config:
    """Look for .claude-lint.json at start or any parent; return merged config."""
    cfg = Config()
    cur = start.resolve()
    while True:
        candidate = cur / ".claude-lint.json"
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
            cfg.max_memory_lines = int(data.get("max_memory_lines", cfg.max_memory_lines))
            cfg.max_claude_md_lines = int(data.get("max_claude_md_lines", cfg.max_claude_md_lines))
            cfg.max_skill_lines = int(data.get("max_skill_lines", cfg.max_skill_lines))
            cfg.min_description_chars = int(
                data.get("min_description_chars", cfg.min_description_chars)
            )
            cfg.max_description_chars = int(
                data.get("max_description_chars", cfg.max_description_chars)
            )
            cfg.disabled_rules = set(data.get("disabled_rules", []))
            cfg.extra_tools = set(data.get("extra_tools", []))
            break
        if cur.parent == cur:
            break
        cur = cur.parent
    return cfg
