"""GenConfig data types (port of ``genconfig/GenConfig.ts``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from emf import EClass, EPackage, EStructuralFeature

GenConfigMode = Literal["emf", "decorator", "plain"]
GenConfigPropertyMode = Literal["editable", "readonly", "none"]


@dataclass
class GenerationSettings:
    mode: GenConfigMode = "emf"
    output_dir: str = "./generated"
    file_extension: str | None = ".py"
    header_comment: str | None = None


@dataclass
class PackageSettings:
    prefix: str = ""
    base_package: str | None = None
    generate_factory: bool = True
    generate_package: bool = True
    generate_index: bool = True


@dataclass
class ClassDefaults:
    generate_interface: bool = True
    generate_impl: bool = True
    root_extends_class: str = "EObject"
    root_extends_interface: str = "EObject"


@dataclass
class FeatureDefaults:
    notify: bool = True
    property: GenConfigPropertyMode = "editable"


@dataclass
class FeatureOverride:
    ecore_feature: EStructuralFeature
    notify: bool | None = None
    property: GenConfigPropertyMode | None = None
    custom_getter: str | None = None
    custom_setter: str | None = None


@dataclass
class ClassOverride:
    ecore_class: EClass
    generate_interface: bool | None = None
    generate_impl: bool | None = None
    extends_class: str | None = None
    implements_interfaces: list[str] | None = None
    feature_overrides: list[FeatureOverride] = field(default_factory=list)


@dataclass
class GenConfig:
    ecore_package: EPackage
    generation: GenerationSettings
    package: PackageSettings
    class_defaults: ClassDefaults | None = None
    feature_defaults: FeatureDefaults | None = None
    class_overrides: list[ClassOverride] = field(default_factory=list)


def create_default_generation_settings() -> GenerationSettings:
    return GenerationSettings()


def create_default_package_settings(prefix: str) -> PackageSettings:
    return PackageSettings(prefix=prefix)


def create_default_class_defaults() -> ClassDefaults:
    return ClassDefaults()


def create_default_feature_defaults(mode: GenConfigMode) -> FeatureDefaults:
    return FeatureDefaults(notify=(mode == "emf"))
