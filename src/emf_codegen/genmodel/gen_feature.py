"""GenFeature (port of ``genmodel/GenFeature.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from emf_codegen.genmodel.generation_mode import PropertyMode

if TYPE_CHECKING:
    from emf import EStructuralFeature


@dataclass
class GenFeature:
    """Generation configuration for an EAttribute or EReference."""

    ecore_feature: EStructuralFeature
    property: PropertyMode = PropertyMode.EDITABLE
    notify: bool = True
    children: bool = False
    create_child: bool = False
    property_sort_choices: bool = False
    getter_name: str | None = None
    setter_name: str | None = None
    documentation: str | None = None


def create_default_gen_feature(feature: EStructuralFeature) -> GenFeature:
    return GenFeature(ecore_feature=feature)
