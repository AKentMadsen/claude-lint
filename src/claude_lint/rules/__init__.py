from __future__ import annotations

from claude_lint.config import Config
from claude_lint.models import ClaudeTree, Finding

from . import cross_refs, frontmatter as fm_rules, hygiene, settings as settings_rules


def run_all(tree: ClaudeTree, cfg: Config) -> list[Finding]:
    findings: list[Finding] = []
    findings += fm_rules.check(tree, cfg)
    findings += cross_refs.check(tree, cfg)
    findings += hygiene.check(tree, cfg)
    findings += settings_rules.check(tree, cfg)
    return [f for f in findings if f.rule_id not in cfg.disabled_rules]
