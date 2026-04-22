# claude-lint

A zero-dependency structural linter for `.claude/` directories. Validates skills, agents,
commands, hooks, memory, and settings against the conventions Claude Code actually enforces
at runtime — complements security-focused tools (AgentShield) and AI-judgment audits
(skill-stocktake) instead of overlapping with them.

## What it checks

| Rule  | Severity | Description |
|-------|----------|-------------|
| CL001 | error    | Frontmatter parse error |
| CL002 | error    | Missing required frontmatter field (e.g. `description`) |
| CL003 | warn     | Description too short (hurts autoload matching) |
| CL004 | warn     | Description too long (inflates prompt tokens) |
| CL005 | warn     | `name` field does not match filename / directory name |
| CL006 | error    | `tools` references a tool that does not exist |
| CL007 | warn     | `model` is stale (`claude-3-*`) or unrecognized |
| CL010 | error    | `MEMORY.md` links to a file that does not exist |
| CL011 | warn     | Memory file exists but is not indexed in `MEMORY.md` |
| CL012 | warn     | Duplicate skill/agent name |
| CL020 | warn     | `MEMORY.md` exceeds line budget (default 200; truncated beyond) |
| CL021 | warn     | `CLAUDE.md` exceeds line budget (default 500) |
| CL022 | warn     | `SKILL.md` exceeds line budget (default 800) |
| CL030 | error    | `settings.json` does not parse |
| CL031 | error    | Unknown hook event name |
| CL032 | error    | Hook command references missing script |
| CL033 | warn     | `permissions.allow` references an unknown tool |

## Install

No install needed — run from a clone:

```bash
git clone <this repo> claude-lint
cd claude-lint
python3 -m claude_lint /path/to/project
```

Or install it as a CLI:

```bash
pip install -e .
claude-lint /path/to/project
```

## Usage

```bash
# lint the current project
claude-lint .

# lint a specific .claude directory
claude-lint ~/.claude

# scan every project under a workspace parent (one level deep)
claude-lint "/Users/you/Projects"

# CI-friendly: JSON output + exit non-zero only on errors
claude-lint . --format json --fail-on error

# include info-level findings
claude-lint . --min-severity info
```

Exit codes:
- `0` — clean, or `--fail-on none`
- `1` — at least one finding at or above `--fail-on` severity (default `error`)
- `2` — path did not exist / no `.claude` dir found

## Configuration

Drop a `.claude-lint.json` at your project root (or any parent). Schema:

```json
{
  "max_memory_lines": 200,
  "max_claude_md_lines": 500,
  "max_skill_lines": 800,
  "min_description_chars": 20,
  "max_description_chars": 400,
  "disabled_rules": ["CL004"],
  "extra_tools": ["CustomMcpTool"]
}
```

## Running against your setups

The CLI supports three input shapes:

1. **A project root** — looks for `./.claude/`.
2. **A `.claude/` dir directly** — handy for `~/.claude`.
3. **A workspace parent** — scans every `*/.claude/` one level down.

For your workspace:

```bash
claude-lint "/Users/kentmadsen/Library/CloudStorage/OneDrive-AuditdataAD/Kent Project"
```

## Tests

```bash
pip install pytest
pytest
```

## Scope

**In scope:** deterministic structural checks — schema, cross-refs, size, known-value lists.

**Out of scope:** security (use AgentShield / `/security-scan`), subjective quality
(overlap, "is this description good" — use `/skill-stocktake`), auto-fix.
