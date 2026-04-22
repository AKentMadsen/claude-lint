from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: Path
    line: int | None = None

    def location(self) -> str:
        if self.line is not None:
            return f"{self.path}:{self.line}"
        return str(self.path)


@dataclass
class ParsedFile:
    path: Path
    frontmatter: dict | None
    body: str
    frontmatter_start_line: int | None = None
    frontmatter_error: str | None = None
    line_count: int = 0


@dataclass
class ClaudeTree:
    root: Path
    skills: list[ParsedFile] = field(default_factory=list)
    agents: list[ParsedFile] = field(default_factory=list)
    commands: list[ParsedFile] = field(default_factory=list)
    claude_md: ParsedFile | None = None
    memory_index: ParsedFile | None = None
    memory_files: list[ParsedFile] = field(default_factory=list)
    settings: list[tuple[Path, dict | None, str | None]] = field(default_factory=list)
    hooks_dir: Path | None = None
