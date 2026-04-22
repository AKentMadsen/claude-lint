"""Minimal YAML-frontmatter parser.

Handles the subset actually used in .claude/ files:
  - scalar values: key: value (bare, single-quoted, double-quoted)
  - flow lists:    key: [a, b, c]
  - block lists:   key:\n  - a\n  - b
  - booleans and integers where obvious

Returns (frontmatter_dict_or_None, body_str, error_or_None).
If the file has no frontmatter, frontmatter_dict is None and error is None.
"""
from __future__ import annotations

import re


_BOOLS = {"true": True, "false": False, "yes": True, "no": False}


def _coerce(raw: str):
    s = raw.strip()
    if not s:
        return ""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    low = s.lower()
    if low in _BOOLS:
        return _BOOLS[low]
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            return s
    return s


def _parse_flow_list(s: str) -> list:
    inner = s.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        return [_coerce(s)]
    inner = inner[1:-1].strip()
    if not inner:
        return []
    items = []
    depth = 0
    buf = []
    in_quote = None
    for ch in inner:
        if in_quote:
            buf.append(ch)
            if ch == in_quote:
                in_quote = None
            continue
        if ch in ("'", '"'):
            in_quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(_coerce("".join(buf)))
            buf = []
        else:
            buf.append(ch)
    if buf:
        items.append(_coerce("".join(buf)))
    return items


def parse(text: str) -> tuple[dict | None, str, str | None, int | None]:
    """Parse frontmatter from text.

    Returns (frontmatter, body, error, frontmatter_start_line).
    frontmatter_start_line is the 1-based line of the opening '---'.
    """
    if not text.startswith("---"):
        return None, text, None, None

    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text, None, None

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None, text, "unterminated frontmatter (no closing ---)", 1

    fm_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :])

    data: dict = {}
    i = 0
    current_key = None
    try:
        while i < len(fm_lines):
            raw = fm_lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            # block-list continuation
            if stripped.startswith("- ") and current_key is not None:
                data.setdefault(current_key, [])
                if not isinstance(data[current_key], list):
                    return None, text, f"mixed list/scalar for {current_key}", 1
                data[current_key].append(_coerce(stripped[2:]))
                i += 1
                continue
            if ":" not in stripped:
                return None, text, f"expected key: value on line {i + 2}", 1
            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()
            current_key = key
            if not rest:
                # could be a block list next
                data[key] = []
                i += 1
                continue
            if rest.startswith("["):
                data[key] = _parse_flow_list(rest)
            else:
                data[key] = _coerce(rest)
            i += 1
    except Exception as e:  # pragma: no cover
        return None, text, f"parse error: {e}", 1

    # Clean empty placeholder lists that were actually scalars
    for k, v in list(data.items()):
        if v == [] and f"{k}:" in text and f"{k}:\n" not in text:
            data[k] = ""
    return data, body, None, 1
