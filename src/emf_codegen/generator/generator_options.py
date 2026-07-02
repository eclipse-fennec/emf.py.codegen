"""GeneratorOptions (port of ``generator/GeneratorOptions.ts``)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GeneratorOptions:
    """Options controlling code generation."""

    output_directory: str = "./generated"
    overwrite: bool = True
    file_header: str | None = None
    indent_size: int = 4
    #: nsURI -> Python import module for referenced packages.
    referenced_packages: dict[str, str] = field(default_factory=dict)


def create_default_options(**overrides: object) -> GeneratorOptions:
    opts = GeneratorOptions()
    for key, value in overrides.items():
        if value is not None and hasattr(opts, key):
            setattr(opts, key, value)
    return opts
