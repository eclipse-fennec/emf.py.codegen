"""Mode-specific generators (mirrors ``generator/modes/``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from emf_codegen.generator.modes.base_generator import BaseGenerator
from emf_codegen.generator.modes.decorator_generator import DecoratorGenerator
from emf_codegen.generator.modes.emf_generator import EmfGenerator
from emf_codegen.generator.modes.plain_generator import PlainGenerator
from emf_codegen.genmodel import GenerationMode

if TYPE_CHECKING:
    from emf_codegen.generator.generator_context import GeneratorContext

__all__ = [
    "BaseGenerator",
    "DecoratorGenerator",
    "EmfGenerator",
    "PlainGenerator",
    "mode_generator_for",
]


def mode_generator_for(mode: GenerationMode, context: GeneratorContext) -> BaseGenerator | None:
    """Return the generator for ``mode``, or None if unsupported."""
    if mode is GenerationMode.PLAIN:
        return PlainGenerator(context)
    if mode is GenerationMode.DECORATOR:
        return DecoratorGenerator(context)
    if mode is GenerationMode.EMF:
        return EmfGenerator(context)
    return None
