"""GenModel (port of ``genmodel/GenModel.ts``).

Root generation configuration. Defaults are adapted to Python/EMFPy (e.g. the
root base class is EMFPy's ``EObject``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from emf_codegen.genmodel.generation_mode import GenerationMode

if TYPE_CHECKING:
    from emf_codegen.genmodel.gen_package import GenPackage

FeatureDelegation = Literal["None", "Virtual", "Reflective"]


@dataclass
class GenModel:
    """Root generation model configuration."""

    model_directory: str = "./generated"
    edit_directory: str | None = None
    editor_directory: str | None = None
    model_plugin_id: str | None = None
    generation_mode: GenerationMode = GenerationMode.DECORATOR
    generate_interfaces: bool = True
    generate_classes: bool = True
    generate_factory: bool = True
    generate_package: bool = True
    generate_resource: bool = False
    bounded_generic_type_names: bool = False
    copyright_text: str | None = None
    gen_packages: list[GenPackage] = field(default_factory=list)
    used_gen_packages: list[GenPackage] = field(default_factory=list)
    import_manager: str | None = None
    feature_delegation: FeatureDelegation = "None"
    root_extends_class: str = "EObject"
    root_extends_interface: str = "EObject"
    root_implements_interface: str | None = None
    suppress_emf_types: bool = False
    suppress_gen_model_annotations: bool = False


def create_default_gen_model() -> GenModel:
    return GenModel()
