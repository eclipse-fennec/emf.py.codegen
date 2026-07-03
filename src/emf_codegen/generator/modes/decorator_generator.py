"""DecoratorGenerator — dataclasses carrying Ecore metadata.

Port of ``modes/DecoratorGenerator.ts``. The TS mode uses ``@ModelClass`` /
``@Attribute`` / ``@Reference`` decorators backed by reflect-metadata; EMFPy has
no per-field decorator framework, so the idiomatic Python equivalent attaches
metadata via an ``ECLASS_URI`` class variable and ``dataclasses.field(metadata=…)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from emf_codegen.generator.import_resolver import module_name
from emf_codegen.generator.modes.base_generator import BaseGenerator
from emf_codegen.util.string_utils import indent_body, make_safe_identifier

if TYPE_CHECKING:
    from emf_codegen.generator.generated_file import GeneratedFile
    from emf_codegen.genmodel import GenClass, GenEnum, GenPackage


class DecoratorGenerator(BaseGenerator):
    """Generates metadata-annotated Python dataclasses."""

    generates_interfaces = False

    def mode_dir(self) -> str:
        return "decorator"

    def generate_class(self, gen_class: GenClass, gen_package: GenPackage) -> GeneratedFile:
        e_class = gen_class.ecore_class
        name = gen_class.impl_class_name or e_class.name or "Unknown"
        ns_uri = gen_package.ecore_package.ns_uri or ""
        imports = self.context.import_resolver.resolve_for_class(gen_class, gen_package)
        super_types = [s.name for s in e_class.e_super_types if s.name]

        content = self.render(
            "class.py.jinja",
            name=name,
            doc=gen_class.documentation or name,
            eclass_uri=f"{ns_uri}#//{name}",
            base=super_types[0] if super_types else None,
            runtime_imports=imports.runtime,
            type_checking_imports=imports.type_checking,
            fields=[self._field(gf.ecore_feature) for gf in gen_class.gen_features],
            operations=[self._operation(go) for go in gen_class.gen_operations],
        )
        return self.create_file(self.module_path(gen_package.base_package, name), content)

    def generate_enum(self, gen_enum: GenEnum, gen_package: GenPackage) -> GeneratedFile:
        e_enum = gen_enum.ecore_enum
        name = e_enum.name or "Unknown"
        members = [
            {
                "name": make_safe_identifier(lit.name or f"VALUE_{lit.value}"),
                "value": f'"{lit.literal or lit.name}"'
                if gen_enum.use_string_values
                else str(lit.value),
            }
            for lit in e_enum.e_literals
        ]
        content = self.render(
            "enum.py.jinja",
            name=name,
            doc=gen_enum.documentation or name,
            members=members,
            string_values=gen_enum.use_string_values,
        )
        return self.create_file(self.module_path(gen_package.base_package, name), content)

    def generate_package_file(self, gen_package: GenPackage) -> GeneratedFile:
        exports = [
            {"module": module_name(gc.ecore_class.name or ""), "name": gc.ecore_class.name}
            for gc in gen_package.gen_classes
            if gc.ecore_class.name
        ]
        exports += [
            {"module": module_name(ge.ecore_enum.name or ""), "name": ge.ecore_enum.name}
            for ge in gen_package.gen_enums
            if ge.ecore_enum.name
        ]
        content = self.render("package.py.jinja", exports=exports)
        directory = self.package_dir(gen_package.base_package)
        path = f"{directory}/__init__.py" if directory else "__init__.py"
        return self.create_file(path, content)

    # ----- helpers ---------------------------------------------------------

    def _field(self, feature: Any) -> dict[str, str]:
        mapper = self.context.type_mapper
        base_type = mapper.map_feature_base_type(feature)
        default = mapper.get_default_value(feature)
        if mapper.is_enum(feature.e_type):
            kind = "enum"
        elif mapper.is_reference(feature):
            kind = "reference"
        else:
            kind = "attribute"
        metadata = f'{{"kind": "{kind}", "type": "{base_type}", "many": {feature.many}}}'
        if feature.many:
            type_ann = f"list[{base_type}]"
            field_expr = f"field(default_factory=list, metadata={metadata})"
        elif default == "None":
            type_ann = f"{base_type} | None"
            field_expr = f"field(default=None, metadata={metadata})"
        else:
            type_ann = base_type
            field_expr = f"field(default={default}, metadata={metadata})"
        return {
            "name": make_safe_identifier(feature.name or "field"),
            "type": type_ann,
            "field_expr": field_expr,
        }

    def _operation(self, gen_op: Any) -> dict[str, Any]:
        op = gen_op.ecore_operation
        mapper = self.context.type_mapper
        params = "".join(
            f", {make_safe_identifier(p.name or 'arg')}: {mapper.map_classifier(p.e_type)}"
            for p in op.e_parameters
        )
        return_type = mapper.map_classifier(op.e_type) if op.e_type is not None else "None"
        return {
            "name": make_safe_identifier(op.name or "op"),
            "params": params,
            "return_type": return_type,
            "body_lines": indent_body(gen_op.body) if gen_op.generate_body else None,
        }
