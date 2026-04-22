from pathlib import Path

from claude_lint import loader, rules
from claude_lint.config import Config


def test_name_prefix_is_accepted(tmp_path: Path):
    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: devtools-my-skill\n"
        "description: A skill with a category prefix that should be accepted.\n"
        "---\nbody\n"
    )
    cfg = Config(name_prefixes=["devtools-", "ai-"])
    tree = loader.load(tmp_path / ".claude", cfg)
    findings = rules.run_all(tree, cfg)
    assert "CL005" not in {f.rule_id for f in findings}


def test_non_claude_layout_with_config(tmp_path: Path):
    # repo layout: agents/ and skill-library/<category>/<skill>/SKILL.md at root
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "helper.md").write_text(
        "---\n"
        "name: helper\n"
        "description: A root-level agent, not under .claude/.\n"
        "---\nbody\n"
    )
    sk = tmp_path / "skill-library" / "07-devtools" / "foo"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: foo\ndescription: A deeply nested skill file.\n---\n"
    )
    cfg = Config(
        agents_dirs=["agents"],
        skills_dirs=["skill-library"],
        recursive_skills=True,
    )
    dirs = loader.find_claude_dirs(tmp_path, cfg)
    assert dirs == [tmp_path.resolve()]
    tree = loader.load(dirs[0], cfg)
    assert len(tree.agents) == 1
    assert len(tree.skills) == 1
    findings = rules.run_all(tree, cfg)
    assert findings == []


def test_bare_dirname_rejected_when_prefixes_required(tmp_path: Path):
    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: my-skill\n"
        "description: Bare dirname with no prefix — should be flagged.\n"
        "---\n"
    )
    cfg = Config(name_prefixes=["devtools-", "ai-"])
    tree = loader.load(tmp_path / ".claude", cfg)
    findings = rules.run_all(tree, cfg)
    assert "CL005" in {f.rule_id for f in findings}


def test_bare_dirname_accepted_without_prefixes(tmp_path: Path):
    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: my-skill\n"
        "description: No prefixes configured — bare dirname should pass.\n"
        "---\n"
    )
    cfg = Config()
    tree = loader.load(tmp_path / ".claude", cfg)
    findings = rules.run_all(tree, cfg)
    assert "CL005" not in {f.rule_id for f in findings}


def test_folded_scalar_agent_does_not_trigger_parse_error(tmp_path: Path):
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "accessibility.md").write_text(
        "---\n"
        "name: accessibility\n"
        "description: >\n"
        "  Multi-line folded description\n"
        "  that spans several lines.\n"
        "model: opus\n"
        "---\nbody\n"
    )
    cfg = Config()
    tree = loader.load(tmp_path / ".claude", cfg)
    findings = rules.run_all(tree, cfg)
    assert "CL001" not in {f.rule_id for f in findings}
