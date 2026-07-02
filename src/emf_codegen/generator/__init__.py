"""Code generation core (mirrors ``generator/``)."""

from emf_codegen.generator.code_generator import CodeGenerator, GenerationResult
from emf_codegen.generator.generated_file import GeneratedFile
from emf_codegen.generator.generator_context import Diagnostic, GeneratorContext
from emf_codegen.generator.generator_options import GeneratorOptions, create_default_options
from emf_codegen.generator.import_resolver import ImportResolver
from emf_codegen.generator.type_mapper import TypeMapper

__all__ = [
    "CodeGenerator",
    "GenerationResult",
    "GeneratedFile",
    "GeneratorContext",
    "Diagnostic",
    "GeneratorOptions",
    "create_default_options",
    "ImportResolver",
    "TypeMapper",
]
