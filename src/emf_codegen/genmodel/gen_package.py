"""GenPackage (port of ``genmodel/GenPackage.ts``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from emf_codegen.util.string_utils import capitalize

if TYPE_CHECKING:
    from emf import EPackage

    from emf_codegen.genmodel.gen_class import GenClass
    from emf_codegen.genmodel.gen_datatype import GenDataType
    from emf_codegen.genmodel.gen_enum import GenEnum


@dataclass
class GenPackage:
    """Generation configuration for an EPackage."""

    ecore_package: EPackage
    prefix: str = ""
    base_package: str = ""
    interface_package_suffix: str = ""
    class_package_suffix: str = "impl"
    adapter_factory: bool = False
    generate_resource_factory: bool = False
    file_extension: str = ""
    content_type_identifier: str | None = None
    gen_classes: list[GenClass] = field(default_factory=list)
    gen_enums: list[GenEnum] = field(default_factory=list)
    gen_data_types: list[GenDataType] = field(default_factory=list)
    nested_gen_packages: list[GenPackage] = field(default_factory=list)
    documentation: str | None = None


def create_default_gen_package(e_package: EPackage) -> GenPackage:
    name = e_package.name or "model"
    return GenPackage(
        ecore_package=e_package,
        prefix=capitalize(name),
        file_extension=name.lower(),
    )
