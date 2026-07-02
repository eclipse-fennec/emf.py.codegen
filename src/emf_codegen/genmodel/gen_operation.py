"""GenOperation (port of ``genmodel/GenOperation.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emf import EOperation


@dataclass
class GenOperation:
    """Generation configuration for an EOperation."""

    ecore_operation: EOperation
    generate_body: bool = False
    body: str | None = None
    documentation: str | None = None


def create_default_gen_operation(operation: EOperation) -> GenOperation:
    return GenOperation(ecore_operation=operation)
