"""ImportResolver — compute Python imports for a generated class.

Much simpler than the TS ``ImportResolver`` (which juggles ``.js`` paths and
barrels). For Python it splits imports into:

- **runtime** imports — enums (needed for default values), ``datetime``, ``Any``;
- **TYPE_CHECKING** imports — sibling classes referenced only in annotations,
  which avoids the circular imports that mutually-referential Ecore models cause.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from emf import EClass, EEnum

from emf_codegen.util.string_utils import to_lower_snake

if TYPE_CHECKING:
    from emf_codegen.genmodel import GenClass, GenPackage


def module_name(type_name: str) -> str:
    """Python module file stem for a generated type (snake_case)."""
    return to_lower_snake(type_name)


@dataclass
class ResolvedImports:
    runtime: list[str] = field(default_factory=list)
    type_checking: list[str] = field(default_factory=list)


class ImportResolver:
    """Resolves the imports a generated class needs."""

    def resolve_for_class(self, gen_class: GenClass, gen_package: GenPackage) -> ResolvedImports:
        e_class = gen_class.ecore_class
        own_name = e_class.name
        local_names = {c.name for c in gen_package.ecore_package.e_classifiers}

        # Super types must be importable at runtime (used as base classes);
        # feature-referenced classes are needed only for annotations.
        super_types: set[str] = set()
        for sup in e_class.e_super_types:
            if sup.name and sup.name != own_name and sup.name in local_names:
                super_types.add(sup.name)

        classes: set[str] = set()
        enums: set[str] = set()
        needs_datetime = False
        needs_any = False
        for feature in e_class.e_structural_features:
            e_type = feature.e_type
            if e_type is None:
                continue
            name = e_type.name
            if name == "EDate":
                needs_datetime = True
            elif name in ("EJavaObject", "EJavaClass", "EFeatureMapEntry"):
                needs_any = True
            elif isinstance(e_type, EEnum) and name and name in local_names:
                enums.add(name)
            elif (
                isinstance(e_type, EClass)
                and name
                and name != own_name
                and name in local_names
                and name not in super_types
            ):
                classes.add(name)

        runtime: list[str] = []
        if needs_datetime:
            runtime.append("from datetime import datetime")
        if needs_any:
            runtime.append("from typing import Any")
        for name in sorted(super_types):
            runtime.append(f"from .{module_name(name)} import {name}")
        for enum_name in sorted(enums):
            runtime.append(f"from .{module_name(enum_name)} import {enum_name}")

        type_checking = [f"from .{module_name(name)} import {name}" for name in sorted(classes)]
        return ResolvedImports(runtime=runtime, type_checking=type_checking)
