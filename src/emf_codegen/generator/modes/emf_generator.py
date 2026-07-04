"""EmfGenerator — EMF-conformant, concrete typed Python classes.

Port of ``modes/EmfGenerator.ts``. Emits, per package:

- one Python ``Enum`` per ``EEnum``;
- one concrete class per ``EClass`` (an ``emf.EObject`` subclass) with typed
  ``@property`` accessors that delegate to ``e_get``/``e_set`` — so the full EMF
  runtime semantics (opposites, containment, container refs, notification) apply
  while client code gets a typed, autocomplete-friendly API;
- a ``<prefix>_package`` module holding the ``EPackage`` plus class/feature
  *literals* (``BOOK``, ``BOOK__TITLE`` …), wired and registered;
- a ``<prefix>_factory`` module; and an ``__init__`` barrel.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from emf import EClass, EEnum, EReference

from emf_codegen.generator.generated_file import GeneratedFile
from emf_codegen.generator.modes.base_generator import BaseGenerator
from emf_codegen.util.string_utils import (
    indent_body,
    make_safe_identifier,
    to_lower_snake,
    to_upper_snake,
)

if TYPE_CHECKING:
    from emf_codegen.genmodel import GenClass, GenEnum, GenPackage

_ECORE_DATATYPES = {
    "EString", "EBoolean", "EInt", "EDouble", "EFloat", "ELong", "EShort",
    "EByte", "EChar", "EDate", "EBigDecimal", "EBigInteger", "EJavaObject",
}


class EmfGenerator(BaseGenerator):
    """Generates concrete EObject subclasses + package/factory/barrel modules."""

    generates_interfaces = False

    def mode_dir(self) -> str:
        return "emf"

    # ----- enums -----------------------------------------------------------

    def generate_enum(self, gen_enum: GenEnum, gen_package: GenPackage) -> GeneratedFile:
        e_enum = gen_enum.ecore_enum
        name = e_enum.name or "Unknown"
        lines = [
            self._header(),
            "from __future__ import annotations",
            "",
            "from enum import Enum",
            "",
            "",
            f"class {name}(Enum):",
            f'    """{gen_enum.documentation or name}"""',
            "",
        ]
        for lit in e_enum.e_literals:
            member = make_safe_identifier(lit.name or f"VALUE_{lit.value}")
            value = f'"{lit.literal or lit.name}"' if gen_enum.use_string_values else str(lit.value)
            lines.append(f"    {member} = {value}")
        return self.create_file(
            self.module_path(gen_package.base_package, name), "\n".join(lines) + "\n"
        )

    # ----- concrete classes ------------------------------------------------

    def generate_class(self, gen_class: GenClass, gen_package: GenPackage) -> GeneratedFile:
        e_class = gen_class.ecore_class
        name = e_class.name or "Unknown"
        pkg_module = self._package_module(gen_package)
        mapper = self.context.type_mapper

        # Base class: first local non-interface super type, else EObject.
        local = {c.name for c in gen_package.ecore_package.e_classifiers}
        supers = [s for s in e_class.e_super_types if s.name in local and not s.interface]
        base = (supers[0].name if supers else None) or "EObject"

        # Imports.
        runtime: list[str] = ["from typing import cast"]
        type_checking: list[str] = []
        if supers:
            runtime.append(f"from .{to_lower_snake(base)} import {base}")
        else:
            runtime.append("from emf import EObject")
        enums, ref_classes, needs_elist, needs_datetime, needs_any = self._feature_type_deps(
            gen_class, gen_package
        )
        for enum_name in sorted(enums):
            runtime.append(f"from .{to_lower_snake(enum_name)} import {enum_name}")
        if needs_datetime:
            runtime.append("from datetime import datetime")
        if needs_any:
            type_checking.append("from typing import Any")
        if needs_elist:
            type_checking.append("from emf import EList")
        for ref in sorted(ref_classes):
            type_checking.append(f"from .{to_lower_snake(ref)} import {ref}")

        # Literal imports from the package module.
        class_upper = to_upper_snake(name)
        literals = [class_upper] + [
            f"{class_upper}__{to_upper_snake(gf.ecore_feature.name or 'f')}"
            for gf in gen_class.gen_features
        ]

        lines = [self._header(), "from __future__ import annotations", ""]
        for imp in runtime:
            lines.append(imp)
        lines.append(self._literal_import(pkg_module, literals))
        if type_checking:
            lines.append("")
            lines.append("from typing import TYPE_CHECKING")
            lines.append("")
            lines.append("if TYPE_CHECKING:")
            for imp in sorted(type_checking):
                lines.append(f"    {imp}")
        lines.append("")
        lines.append("")
        lines.append(f"class {name}({base}):")
        lines.append(f'    """{gen_class.documentation or name}"""')
        lines.append("")
        lines.append("    def __init__(self) -> None:")
        lines.append("        super().__init__()")
        lines.append(f"        self._eclass = {class_upper}")

        for gf in gen_class.gen_features:
            lines.append("")
            lines.extend(self._accessor(gf, class_upper, mapper))

        for go in gen_class.gen_operations:
            lines.append("")
            lines.extend(self._operation(go, mapper))

        return self.create_file(
            self.module_path(gen_package.base_package, name), "\n".join(lines) + "\n"
        )

    def _accessor(self, gen_feature: Any, class_upper: str, mapper: Any) -> list[str]:
        feature = gen_feature.ecore_feature
        fname = make_safe_identifier(feature.name or "field")
        literal = f"{class_upper}__{to_upper_snake(feature.name or 'f')}"
        base_type = mapper.map_feature_base_type(feature)

        if feature.many:
            ann = f"EList[{base_type}]"
        elif mapper.get_default_value(feature) == "None":
            ann = f"{base_type} | None"
        else:
            ann = base_type

        out = [
            "    @property",
            f"    def {fname}(self) -> {ann}:",
            f'        return cast("{ann}", self.e_get({literal}))',
        ]
        # Many features expose the live EList (mutate in place); no setter. Readonly
        # features omit the setter too.
        if not feature.many and gen_feature.property.value != "readonly":
            out += [
                "",
                f"    @{fname}.setter",
                f"    def {fname}(self, value: {ann}) -> None:",
                f"        self.e_set({literal}, value)",
            ]
        return out

    def _operation(self, gen_op: Any, mapper: Any) -> list[str]:
        op = gen_op.ecore_operation
        params = "".join(
            f", {make_safe_identifier(p.name or 'arg')}: {mapper.map_classifier(p.e_type)}"
            for p in op.e_parameters
        )
        ret = mapper.map_classifier(op.e_type) if op.e_type is not None else "None"
        op_name = make_safe_identifier(op.name or "op")
        lines = [f"    def {op_name}(self{params}) -> {ret}:"]
        if gen_op.generate_body:
            lines.extend(indent_body(gen_op.body))
        else:
            lines.append(f'        raise NotImplementedError("{op_name} not implemented")')
        return lines

    # ----- package (metamodel) module --------------------------------------

    def generate_package_file(self, gen_package: GenPackage) -> GeneratedFile:
        pkg = gen_package.ecore_package
        classes = [c for c in pkg.e_classifiers if isinstance(c, EClass)]
        enums = [c for c in pkg.e_classifiers if isinstance(c, EEnum)]
        cvar = {c.name: to_upper_snake(c.name or "cls") for c in classes}
        evar = {e.name: to_upper_snake(e.name or "enum") for e in enums}

        has_operations = any(c.e_operations for c in classes)

        lines = [self._header(), "from __future__ import annotations", ""]
        lines.append("from emf import (")
        symbols = ["EAttribute", "EClass", "EcoreDataTypes", "EEnum",
                   "EEnumLiteral", "EPackage", "EReference", "PackageRegistry"]
        if has_operations:
            symbols.extend(["EOperation", "EParameter"])
        for sym in symbols:
            lines.append(f"    {sym},")
        lines.append(")")
        for e in enums:
            lines.append(f"from .{to_lower_snake(e.name or 'enum')} import {e.name}")
        lines.append("")
        lines.append("")
        lines.append(f'E_NAME = "{pkg.name or ""}"')
        lines.append(f'E_NS_URI = "{pkg.ns_uri or ""}"')
        lines.append(f'E_NS_PREFIX = "{pkg.ns_prefix or ""}"')
        lines.append("")
        lines.append("PACKAGE = EPackage(E_NAME, ns_uri=E_NS_URI, ns_prefix=E_NS_PREFIX)")
        lines.append("")
        # Enum + class + feature literals (declared before wiring).
        for e in enums:
            lines.append(f'{evar[e.name]} = EEnum("{e.name}")')
        for c in classes:
            lines.append(f'{cvar[c.name]} = EClass("{c.name}", abstract={bool(c.abstract)})')
        lines.append("")
        for c in classes:
            for feature in c.e_structural_features:
                lines.append(self._literal_decl(feature, c, cvar, evar))
        lines.append("")
        lines.append("")
        lines.append("def _init() -> None:")
        body = self._init_body(classes, enums, cvar, evar)
        lines.extend(f"    {line}" if line else "" for line in body)
        lines.append("")
        lines.append("")
        lines.append("_init()")
        lines.append("")
        # Export a deferred creator registration function, called from __init__.py
        # after all classes are loaded (avoids circular imports).
        concrete_classes = [c for c in classes if not c.abstract]
        if concrete_classes:
            lines.append("")
            lines.append("")
            lines.append("def _register_creators() -> None:")
            lines.append('    """Register typed creators — call once from __init__."""')
            lines.append("    _factory = PACKAGE.e_factory_instance")
            for c in concrete_classes:
                mod = to_lower_snake(c.name or "cls")
                lines.append(f"    from .{mod} import {c.name}")
                lines.append(f"    _factory.register_creator({cvar[c.name]}, lambda _ec, _C={c.name}: _C())")
        path = self._module_in(gen_package, f"{self._package_module(gen_package)}.py")
        return self.create_file(path, "\n".join(lines) + "\n")

    def _literal_decl(
        self, feature: Any, owner: Any, cvar: dict[Any, str], evar: dict[Any, str]
    ) -> str:
        lit = f"{cvar[owner.name]}__{to_upper_snake(feature.name or 'f')}"
        e_type = feature.e_type
        type_name = e_type.name if e_type is not None else None
        if isinstance(feature, EReference):
            target = cvar.get(type_name, "None")
            return f'{lit} = EReference("{feature.name}", {target})'
        if type_name in evar:
            type_expr = evar[type_name]
        elif type_name in _ECORE_DATATYPES:
            type_expr = f"EcoreDataTypes.{type_name}"
        else:
            type_expr = "EcoreDataTypes.EJavaObject"
        return f'{lit} = EAttribute("{feature.name}", {type_expr})'

    def _init_body(
        self, classes: list[Any], enums: list[Any], cvar: dict[Any, str], evar: dict[Any, str]
    ) -> list[str]:
        out: list[str] = []
        # Enum literals (+ Python-enum instance wiring for a typed API).
        for e in enums:
            for lit in e.e_literals:
                member = make_safe_identifier(lit.name or f"VALUE_{lit.value}")
                lit_lit = "None" if lit.literal is None else f'"{lit.literal}"'
                out.append(f"_lit = EEnumLiteral(\"{lit.name}\", value={lit.value}, "
                           f"literal={lit_lit})")
                out.append(f"_lit.instance = {e.name}.{member}")
                out.append(f"{evar[e.name]}.add_literal(_lit)")
        # Features: bounds, containment, default literal, attach to class.
        for c in classes:
            for feature in c.e_structural_features:
                lit = f"{cvar[c.name]}__{to_upper_snake(feature.name or 'f')}"
                if feature.many:
                    out.append(f"{lit}.upper_bound = -1")
                if isinstance(feature, EReference) and feature.containment:
                    out.append(f"{lit}.containment = True")
                if not isinstance(feature, EReference):
                    dvl = feature.default_value_literal
                    if dvl is not None:
                        out.append(f'{lit}.default_value_literal = "{dvl}"')
                out.append(f"{cvar[c.name]}.e_structural_features.add({lit})")
        # Super types.
        for c in classes:
            for sup in c.e_super_types:
                if sup.name in cvar:
                    out.append(f"{cvar[c.name]}.e_super_types.append({cvar[sup.name]})")
        # Opposites.
        for c in classes:
            for feature in c.e_structural_features:
                opp = feature.e_opposite if isinstance(feature, EReference) else None
                if opp is not None and opp.e_containing_class is not None:
                    owner = opp.e_containing_class.name
                    if owner in cvar:
                        lit = f"{cvar[c.name]}__{to_upper_snake(feature.name or 'f')}"
                        olit = f"{cvar[owner]}__{to_upper_snake(opp.name or 'f')}"
                        out.append(f"{lit}.e_opposite = {olit}")
        # Operations: register EOperation objects for reflective discovery.
        for c in classes:
            for op in c.e_operations:
                ret_type = op.e_type.name if op.e_type is not None else None
                ret_expr = self._classifier_expr(ret_type, cvar, evar)
                out.append(f'_op = EOperation("{op.name}", {ret_expr})')
                if op.lower_bound != 0:
                    out.append(f"_op.lower_bound = {op.lower_bound}")
                if op.upper_bound != 1:
                    out.append(f"_op.upper_bound = {op.upper_bound}")
                for param in op.e_parameters:
                    p_type = param.e_type.name if param.e_type is not None else None
                    p_expr = self._classifier_expr(p_type, cvar, evar)
                    out.append(f'_param = EParameter("{param.name}", {p_expr})')
                    if param.lower_bound != 0:
                        out.append(f"_param.lower_bound = {param.lower_bound}")
                    if param.upper_bound != 1:
                        out.append(f"_param.upper_bound = {param.upper_bound}")
                    out.append("_op.e_parameters.add(_param)")
                out.append(f"{cvar[c.name]}.e_operations.add(_op)")
        # Classifiers + registration.
        for e in enums:
            out.append(f"PACKAGE.e_classifiers.add({evar[e.name]})")
        for c in classes:
            out.append(f"PACKAGE.e_classifiers.add({cvar[c.name]})")
        out.append("PackageRegistry.INSTANCE.register_package(PACKAGE)")
        return out

    def _classifier_expr(
        self, type_name: str | None, cvar: dict[Any, str], evar: dict[Any, str]
    ) -> str:
        """Resolve an EOperation return/parameter type to a runtime-classifier
        expression: a local EClass/EEnum literal, an ``EcoreDataTypes`` member,
        or the ``EJavaObject`` fallback for anything not resolvable locally."""
        if type_name is None:
            return "None"
        if type_name in cvar:
            return cvar[type_name]
        if type_name in evar:
            return evar[type_name]
        if type_name in _ECORE_DATATYPES:
            return f"EcoreDataTypes.{type_name}"
        warnings.warn(
            f"Unresolved type '{type_name}' in operation signature, "
            f"falling back to EJavaObject",
            stacklevel=2,
        )
        return "EcoreDataTypes.EJavaObject"

    # ----- factory ---------------------------------------------------------

    def generate_factory(self, gen_package: GenPackage) -> GeneratedFile | None:
        pkg = gen_package.ecore_package
        pkg_module = self._package_module(gen_package)
        concrete = [
            c for c in pkg.e_classifiers
            if isinstance(c, EClass) and not c.abstract and not c.interface
        ]
        lines = [self._header(), "from __future__ import annotations", ""]
        lines.append("from emf import EClass, EObject")
        lines.append(f"from .{pkg_module} import PACKAGE")
        for c in concrete:
            lines.append(f"from .{to_lower_snake(c.name or 'cls')} import {c.name}")
        lines.append("")
        lines.append("")
        lines.append(f"class {gen_package.prefix}Factory:")
        lines.append('    """Factory for creating model objects."""')
        lines.append("")
        lines.append("    PACKAGE = PACKAGE")
        for c in concrete:
            lines.append("")
            lines.append(f"    def create_{to_lower_snake(c.name or 'cls')}(self) -> {c.name}:")
            lines.append(f"        return {c.name}()")
        lines.append("")
        lines.append("    def create(self, e_class: EClass) -> EObject:")
        lines.append("        name = e_class.name")
        for c in concrete:
            lines.append(f'        if name == "{c.name}":')
            lines.append(f"            return {c.name}()")
        lines.append('        raise ValueError(f"Unknown class: {name}")')
        lines.append("")
        lines.append("")
        lines.append(f"FACTORY = {gen_package.prefix}Factory()")
        path = self._module_in(gen_package, f"{to_lower_snake(gen_package.prefix)}_factory.py")
        return self.create_file(path, "\n".join(lines) + "\n")

    # ----- barrel ----------------------------------------------------------

    def generate_index(self, gen_package: GenPackage) -> GeneratedFile | None:
        pkg = gen_package.ecore_package
        pkg_module = self._package_module(gen_package)
        classes = [c for c in pkg.e_classifiers if isinstance(c, EClass)]
        enums = [c for c in pkg.e_classifiers if isinstance(c, EEnum)]
        exports: list[str] = []
        lines = [self._header(), "from __future__ import annotations", ""]
        for e in enums:
            lines.append(f"from .{to_lower_snake(e.name or 'enum')} import {e.name}")
            exports.append(e.name or "")
        for c in classes:
            lines.append(f"from .{to_lower_snake(c.name or 'cls')} import {c.name}")
            exports.append(c.name or "")
        lines.append(f"from .{pkg_module} import PACKAGE")
        factory_module = to_lower_snake(gen_package.prefix) + "_factory"
        lines.append(f"from .{factory_module} import FACTORY, {gen_package.prefix}Factory")
        exports += ["PACKAGE", "FACTORY", f"{gen_package.prefix}Factory"]
        lines.append("")
        lines.append("__all__ = [")
        for name in exports:
            lines.append(f'    "{name}",')
        lines.append("]")
        # Register typed creators now that all classes are loaded
        concrete = [c for c in classes if not c.abstract]
        if concrete:
            lines.append("")
            lines.append(f"from .{pkg_module} import _register_creators")
            lines.append("_register_creators()")
        path = self._module_in(gen_package, "__init__.py")
        return self.create_file(path, "\n".join(lines) + "\n")

    # ----- helpers ---------------------------------------------------------

    def _header(self) -> str:
        return self.context.get_file_header().rstrip("\n") + "\n"

    def _package_module(self, gen_package: GenPackage) -> str:
        return f"{to_lower_snake(gen_package.prefix)}_package"

    def _module_in(self, gen_package: GenPackage, filename: str) -> str:
        directory = self.package_dir(gen_package.base_package)
        return f"{directory}/{filename}" if directory else filename

    def _literal_import(self, pkg_module: str, literals: list[str]) -> str:
        joined = ", ".join(literals)
        return f"from .{pkg_module} import {joined}"

    def _feature_type_deps(
        self, gen_class: GenClass, gen_package: GenPackage
    ) -> tuple[set[str], set[str], bool, bool, bool]:
        local = {c.name for c in gen_package.ecore_package.e_classifiers}
        own = gen_class.ecore_class.name
        enums: set[str] = set()
        ref_classes: set[str] = set()
        needs_elist = needs_datetime = needs_any = False
        for gf in gen_class.gen_features:
            feature = gf.ecore_feature
            if feature.many:
                needs_elist = True
            e_type = feature.e_type
            if e_type is None:
                continue
            tname = e_type.name
            if tname == "EDate":
                needs_datetime = True
            elif tname in ("EJavaObject", "EJavaClass", "EFeatureMapEntry"):
                needs_any = True
            elif isinstance(e_type, EEnum) and tname and tname in local:
                enums.add(tname)
            elif isinstance(e_type, EClass) and tname and tname in local and tname != own:
                ref_classes.add(tname)
        return enums, ref_classes, needs_elist, needs_datetime, needs_any
