from claude_lint import frontmatter


def test_no_frontmatter():
    fm, body, err, line = frontmatter.parse("hello\nworld\n")
    assert fm is None
    assert body == "hello\nworld\n"
    assert err is None


def test_simple_scalars():
    text = "---\nname: foo\ndescription: bar\n---\nbody\n"
    fm, body, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm == {"name": "foo", "description": "bar"}
    assert body == "body\n"


def test_flow_list():
    text = "---\ntools: [Read, Edit, Bash]\n---\n"
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm["tools"] == ["Read", "Edit", "Bash"]


def test_block_list():
    text = "---\ntools:\n  - Read\n  - Edit\n---\n"
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm["tools"] == ["Read", "Edit"]


def test_unterminated():
    fm, _, err, _ = frontmatter.parse("---\nfoo: bar\n")
    assert fm is None
    assert err and "unterminated" in err


def test_quoted_values():
    text = '---\ndescription: "a: colon"\n---\n'
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm["description"] == "a: colon"
