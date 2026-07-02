"""BaseGenerator — Jinja2 rendering + path helpers (port of ``modes/BaseGenerator.ts``)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from emf_codegen.generator.generated_file import GeneratedFile
from emf_codegen.generator.import_resolver import module_name

if TYPE_CHECKING:
    from emf_codegen.generator.generator_context import GeneratorContext
    from emf_codegen.genmodel import GenClass, GenEnum, GenPackage

_TEMPLATES_ROOT = Path(__file__).resolve().parent.parent.parent / "templates"


class BaseGenerator(ABC):
    """Base for mode-specific generators."""

    #: Whether this mode emits separate interface files.
    generates_interfaces: bool = True

    def __init__(self, context: GeneratorContext) -> None:
        self.context = context
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_ROOT / self.mode_dir())),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            autoescape=False,
        )

    @abstractmethod
    def mode_dir(self) -> str:
        """Template subdirectory name for this mode."""

    @abstractmethod
    def generate_class(self, gen_class: GenClass, gen_package: GenPackage) -> GeneratedFile: ...

    @abstractmethod
    def generate_enum(self, gen_enum: GenEnum, gen_package: GenPackage) -> GeneratedFile: ...

    @abstractmethod
    def generate_package_file(self, gen_package: GenPackage) -> GeneratedFile: ...

    def generate_interface(
        self, gen_class: GenClass, gen_package: GenPackage
    ) -> GeneratedFile | None:
        return None

    def generate_factory(self, gen_package: GenPackage) -> GeneratedFile | None:
        return None

    def generate_index(self, gen_package: GenPackage) -> GeneratedFile | None:
        """Emit a barrel/index file (e.g. ``__init__.py``); None if the mode folds
        the barrel into ``generate_package_file``."""
        return None

    # ----- helpers ---------------------------------------------------------

    def render(self, template_name: str, **ctx: Any) -> str:
        template = self._env.get_template(template_name)
        return template.render(header=self.context.get_file_header(), **ctx)

    def create_file(self, path: str, content: str) -> GeneratedFile:
        return GeneratedFile(path, content)

    def package_dir(self, base_package: str) -> str:
        return base_package.replace(".", "/")

    def module_path(self, base_package: str, type_name: str) -> str:
        directory = self.package_dir(base_package)
        filename = f"{module_name(type_name)}.py"
        return f"{directory}/{filename}" if directory else filename
