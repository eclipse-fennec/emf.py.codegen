"""Generation modes (port of ``genmodel/GenerationMode.ts``)."""

from __future__ import annotations

from enum import StrEnum


class GenerationMode(StrEnum):
    """How model code is emitted."""

    #: Plain Python classes (dataclass-style), no runtime dependency.
    PLAIN = "plain"
    #: Classes annotated with EMFPy registry decorators.
    DECORATOR = "decorator"
    #: EMF-conformant classes on the EMFPy runtime (EObject + package + factory).
    EMF = "emf"


class PropertyMode(StrEnum):
    """Property access generated for a feature."""

    NONE = "none"
    READONLY = "readonly"
    EDITABLE = "editable"
