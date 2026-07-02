"""Utilities: string helpers and reflective EObject accessors."""

from emf_codegen.util import eobject_helper
from emf_codegen.util.string_utils import (
    capitalize,
    escape_string,
    is_reserved_word,
    make_safe_identifier,
    to_camel_case,
    to_lower_snake,
    to_pascal_case,
    to_safe_identifier,
    to_upper_snake,
    uncapitalize,
)

__all__ = [
    "eobject_helper",
    "capitalize",
    "uncapitalize",
    "to_upper_snake",
    "to_lower_snake",
    "to_camel_case",
    "to_pascal_case",
    "escape_string",
    "to_safe_identifier",
    "is_reserved_word",
    "make_safe_identifier",
]
