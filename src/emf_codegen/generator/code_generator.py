"""CodeGenerator — orchestrates generation by mode (port of ``generator/CodeGenerator.ts``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from emf_codegen.generator.generator_context import Diagnostic, GeneratorContext
from emf_codegen.generator.generator_options import GeneratorOptions, create_default_options
from emf_codegen.generator.modes.plain_generator import PlainGenerator
from emf_codegen.genmodel import GenerationMode

if TYPE_CHECKING:
    from emf_codegen.generator.generated_file import GeneratedFile
    from emf_codegen.generator.modes.base_generator import BaseGenerator
    from emf_codegen.genmodel import GenModel, GenPackage


@dataclass
class GenerationResult:
    files: list[GeneratedFile] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    success: bool = True


class CodeGenerator:
    """Generates all files for a :class:`GenModel`."""

    def __init__(self, gen_model: GenModel, **options: Any) -> None:
        self.gen_model = gen_model
        self.context = GeneratorContext(gen_model, _build_options(options))
        self.generator = self._create_mode_generator(gen_model.generation_mode)

    def _create_mode_generator(self, mode: GenerationMode) -> BaseGenerator:
        if mode is GenerationMode.PLAIN:
            return PlainGenerator(self.context)
        # emf / decorator generators arrive in Phase 4.
        from emf_codegen.generator.modes import mode_generator_for

        generator = mode_generator_for(mode, self.context)
        if generator is None:
            raise NotImplementedError(f"Generation mode '{mode}' is not implemented yet")
        return generator

    def generate(self) -> GenerationResult:
        files: list[GeneratedFile] = []
        try:
            for gen_package in self.gen_model.gen_packages:
                files.extend(self._generate_package(gen_package))
        except Exception as exc:  # noqa: BLE001 - surface as a diagnostic
            self.context.error(str(exc))
        return GenerationResult(
            files=files,
            diagnostics=self.context.diagnostics,
            success=not self.context.has_errors(),
        )

    def _generate_package(self, gen_package: GenPackage) -> list[GeneratedFile]:
        files: list[GeneratedFile] = []
        for gen_enum in gen_package.gen_enums:
            files.append(self.generator.generate_enum(gen_enum, gen_package))

        if self.gen_model.generate_interfaces and self.generator.generates_interfaces:
            for gen_class in gen_package.gen_classes:
                if gen_class.generate_interface:
                    file = self.generator.generate_interface(gen_class, gen_package)
                    if file is not None:
                        files.append(file)

        if self.gen_model.generate_classes:
            for gen_class in gen_package.gen_classes:
                if gen_class.generate_impl and not gen_class.ecore_class.interface:
                    files.append(self.generator.generate_class(gen_class, gen_package))

        if self.gen_model.generate_package:
            files.append(self.generator.generate_package_file(gen_package))

        if self.gen_model.generate_factory:
            factory = self.generator.generate_factory(gen_package)
            if factory is not None:
                files.append(factory)

        index = self.generator.generate_index(gen_package)
        if index is not None:
            files.append(index)

        for nested in gen_package.nested_gen_packages:
            files.extend(self._generate_package(nested))
        return files


def _build_options(options: dict[str, Any]) -> GeneratorOptions:
    if "output_directory" in options or options:
        return create_default_options(**options)
    return GeneratorOptions()
