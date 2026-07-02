"""emf-codegen — a Python code generator for Ecore models, built on EMFPy.

Equivalent of the TypeScript ``@emfts/codegen``: it loads an ``.ecore`` model
(via EMFPy's XMI reader) plus a ``.genconfig.xmi`` configuration, builds an
internal generation model, and emits Python source in one of several modes
(plain / emf / decorator) using Jinja2 templates.

The public ``generate`` / ``generate_in_memory`` entry points are assembled here
as the implementation lands. See ``PLAN.md`` for the roadmap.
"""

__version__ = "0.1.0.dev0"

from emf_codegen.genconfig import GenConfigConverter, GenConfigLoader
from emf_codegen.generator import CodeGenerator, GenerationResult
from emf_codegen.loader import EcoreLoader

__all__ = ["__version__", "generate", "generate_in_memory", "GenerationResult"]


def _build(
    ecore_path: str,
    config_path: str,
    dependencies: list[str] | None,
) -> tuple[object, str]:
    ecore_loader = EcoreLoader()
    for dep in dependencies or []:
        ecore_loader.load(dep)
    e_package = ecore_loader.load(ecore_path)

    config_loader = GenConfigLoader()
    config_loader.register_package(e_package)
    config = config_loader.load(config_path)

    gen_model = GenConfigConverter().convert(config)
    return gen_model, config.generation.output_dir


def generate(
    ecore_path: str,
    config_path: str,
    output_dir: str | None = None,
    *,
    write_files: bool = True,
    dependencies: list[str] | None = None,
    referenced_packages: dict[str, str] | None = None,
) -> GenerationResult:
    """Generate Python code from an Ecore model + genconfig, writing files by default."""
    gen_model, config_output = _build(ecore_path, config_path, dependencies)
    out_dir = output_dir or config_output
    generator = CodeGenerator(
        gen_model,  # type: ignore[arg-type]
        output_directory=out_dir,
        referenced_packages=referenced_packages,
    )
    result = generator.generate()
    if write_files and result.success:
        for file in result.files:
            file.write(out_dir)
    return result


def generate_in_memory(
    ecore_path: str,
    config_path: str,
    *,
    dependencies: list[str] | None = None,
    referenced_packages: dict[str, str] | None = None,
) -> GenerationResult:
    """Generate code without writing files."""
    gen_model, config_output = _build(ecore_path, config_path, dependencies)
    generator = CodeGenerator(
        gen_model,  # type: ignore[arg-type]
        output_directory=config_output,
        referenced_packages=referenced_packages,
    )
    return generator.generate()
