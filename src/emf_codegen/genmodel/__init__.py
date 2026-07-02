"""Internal generation model (mirrors ``genmodel/``)."""

from emf_codegen.genmodel.gen_class import GenClass, create_default_gen_class
from emf_codegen.genmodel.gen_datatype import (
    GenDataType,
    create_default_gen_data_type,
    map_default_py_type,
)
from emf_codegen.genmodel.gen_enum import (
    GenEnum,
    GenEnumLiteral,
    create_default_gen_enum,
)
from emf_codegen.genmodel.gen_feature import GenFeature, create_default_gen_feature
from emf_codegen.genmodel.gen_model import GenModel, create_default_gen_model
from emf_codegen.genmodel.gen_operation import (
    GenOperation,
    create_default_gen_operation,
)
from emf_codegen.genmodel.gen_package import GenPackage, create_default_gen_package
from emf_codegen.genmodel.generation_mode import GenerationMode, PropertyMode

__all__ = [
    "GenerationMode",
    "PropertyMode",
    "GenModel",
    "create_default_gen_model",
    "GenPackage",
    "create_default_gen_package",
    "GenClass",
    "create_default_gen_class",
    "GenFeature",
    "create_default_gen_feature",
    "GenEnum",
    "GenEnumLiteral",
    "create_default_gen_enum",
    "GenDataType",
    "create_default_gen_data_type",
    "map_default_py_type",
    "GenOperation",
    "create_default_gen_operation",
]
