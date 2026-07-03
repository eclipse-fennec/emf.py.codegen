"""String helpers for code generation (port of ``util/StringUtils.ts``).

Adapted to Python targets: identifier safety/reserved words follow Python, and
``escape_string`` escapes for Python string literals.
"""

from __future__ import annotations

import keyword
import re
import textwrap


def capitalize(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def uncapitalize(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def to_upper_snake(text: str) -> str:
    if not text:
        return text
    return re.sub(r"([A-Z])", r"_\1", text).upper().lstrip("_")


def to_lower_snake(text: str) -> str:
    if not text:
        return text
    return re.sub(r"([A-Z])", r"_\1", text).lower().lstrip("_")


def _replace_separators(text: str, upper_first_letter_after_sep: bool) -> str:
    def repl(match: re.Match[str]) -> str:
        char = match.group(1)
        return char.upper() if char else ""

    return re.sub(r"[-_\s]+(.)?", repl, text)


def to_camel_case(text: str) -> str:
    if not text:
        return text
    result = _replace_separators(text, True)
    return result[:1].lower() + result[1:]


def to_pascal_case(text: str) -> str:
    if not text:
        return text
    result = _replace_separators(text, True)
    return result[:1].upper() + result[1:]


def escape_string(text: str) -> str:
    """Escape a string for embedding in a generated Python double-quoted literal."""
    if not text:
        return text
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def to_safe_identifier(text: str) -> str:
    if not text:
        return text
    result = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    if result and result[0].isdigit():
        result = "_" + result
    return result


def is_reserved_word(text: str) -> bool:
    """Whether ``text`` is a Python keyword or soft keyword."""
    return keyword.iskeyword(text) or keyword.issoftkeyword(text)


def make_safe_identifier(text: str) -> str:
    """A safe Python identifier; reserved words get a trailing underscore."""
    safe = to_safe_identifier(text)
    return safe + "_" if is_reserved_word(safe) else safe


def indent_body(body: str, indent: str = "        ") -> list[str]:
    """Dedent hand-authored operation-body source and re-indent it for splicing
    into a generated method (blank lines are left empty, not padded)."""
    dedented = textwrap.dedent(body).strip("\n")
    return [f"{indent}{line}" if line.strip() else "" for line in dedented.split("\n")]
