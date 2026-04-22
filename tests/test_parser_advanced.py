from claude_lint import frontmatter


def test_folded_scalar():
    text = (
        "---\n"
        "description: >\n"
        "  Line one of the description\n"
        "  continues on the next line.\n"
        "model: opus\n"
        "---\n"
        "body\n"
    )
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None, err
    assert fm["model"] == "opus"
    assert "Line one" in fm["description"]
    assert "continues" in fm["description"]


def test_literal_scalar():
    text = "---\ndescription: |\n  line1\n  line2\n---\n"
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert "line1\nline2" in fm["description"]


def test_nested_mapping_is_skipped():
    text = (
        "---\n"
        "name: foo\n"
        "metadata:\n"
        "  version: 1.0.3\n"
        "  author: kent\n"
        "description: hello\n"
        "---\n"
    )
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm["name"] == "foo"
    assert fm["description"] == "hello"


def test_scalar_tools_comma_separated_parses():
    text = "---\ndescription: x\ntools: Read, Bash, Grep\n---\n"
    fm, _, err, _ = frontmatter.parse(text)
    assert err is None
    assert fm["tools"] == "Read, Bash, Grep"
