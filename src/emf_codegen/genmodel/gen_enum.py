"""GenEnum / GenEnumLiteral (port of ``genmodel/GenEnum.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emf import EEnum


@dataclass
class GenEnumLiteral:
    """Generation configuration for an EEnumLiteral."""

    name: str
    value: str | int | None = None
    documentation: str | None = None


@dataclass
class GenEnum:
    """Generation configuration for an EEnum."""

    ecore_enum: EEnum
    use_string_values: bool = True
    generate_as_const: bool = False
    documentation: str | None = None


def create_default_gen_enum(e_enum: EEnum) -> GenEnum:
    return GenEnum(ecore_enum=e_enum)
