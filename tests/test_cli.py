import json
from pathlib import Path

from claude_lint import cli

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_good_exits_zero(capsys):
    rc = cli.main([str(FIXTURES / "good")])
    assert rc == 0


def test_cli_bad_exits_nonzero(capsys):
    rc = cli.main([str(FIXTURES / "bad")])
    assert rc == 1


def test_cli_json_output(capsys):
    rc = cli.main([str(FIXTURES / "bad"), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "findings" in data
    assert isinstance(data["findings"], list)
    assert any(f["rule_id"] == "CL010" for f in data["findings"])
    assert rc == 1


def test_cli_fail_on_none_exits_zero():
    rc = cli.main([str(FIXTURES / "bad"), "--fail-on", "none"])
    assert rc == 0
