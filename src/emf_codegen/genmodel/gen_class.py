"""GenClass (port of ``genmodel/GenClass.ts``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emf import EClass

    from emf_codegen.genmodel.gen_feature import GenFeature
    from emf_codegen.genmodel.gen_operation import GenOperation


@dataclass
class GenClass:
    """Generation configuration for an EClass."""

    ecore_class: EClass
    generate_interface: bool = True
    generate_impl: bool = True
    dynamic: bool = False
    impl_class_name: str | None = None
    interface_name: str | None = None
    label_feature: GenFeature | None = None
    base_class: str | None = None
    gen_features: list[GenFeature] = field(default_factory=list)
    gen_operations: list[GenOperation] = field(default_factory=list)
    documentation: str | None = None
    image: str | None = None


def create_default_gen_class(e_class: EClass) -> GenClass:
    return GenClass(ecore_class=e_class)
