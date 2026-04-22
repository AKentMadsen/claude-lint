from pathlib import Path

from claude_lint import loader, rules
from claude_lint.config import Config

FIXTURES = Path(__file__).parent / "fixtures"


def _run(kind: str) -> list:
    tree = loader.load(FIXTURES / kind / ".claude")
    return rules.run_all(tree, Config())


def _ids(findings) -> set[str]:
    return {f.rule_id for f in findings}


def test_good_fixture_has_no_findings():
    findings = _run("good")
    assert findings == [], [str(f) for f in findings]


def test_bad_fixture_triggers_expected_rules():
    ids = _ids(_run("bad"))
    # name mismatch + short description on the skill
    assert "CL003" in ids
    assert "CL005" in ids
    # unknown tool + stale model on the agent
    assert "CL006" in ids
    assert "CL007" in ids
    # settings: unknown hook event + unknown permission tool
    assert "CL031" in ids
    assert "CL033" in ids
    # memory: missing link + orphan
    assert "CL010" in ids
    assert "CL011" in ids


def test_disabled_rule_is_suppressed():
    tree = loader.load(FIXTURES / "bad" / ".claude")
    cfg = Config(disabled_rules={"CL006"})
    findings = rules.run_all(tree, cfg)
    assert "CL006" not in {f.rule_id for f in findings}


def test_extra_tools_allowlist():
    tree = loader.load(FIXTURES / "bad" / ".claude")
    cfg = Config(extra_tools={"Nope", "Bogus"})
    findings = rules.run_all(tree, cfg)
    ids = {f.rule_id for f in findings}
    assert "CL006" not in ids
    assert "CL033" not in ids
