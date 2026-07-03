"""GenConfigConverter — GenConfig → internal GenModel.

Port of ``genconfig/GenConfigConverter.ts`` (data types mapped to Python).
"""

from __future__ import annotations

from emf import EClass, EDataType, EEnum, EOperation, EReference, EStructuralFeature

from emf_codegen.genconfig.gen_config import (
    ClassOverride,
    FeatureOverride,
    GenConfig,
    GenConfigPropertyMode,
)
from emf_codegen.genmodel import (
    GenClass,
    GenDataType,
    GenEnum,
    GenerationMode,
    GenFeature,
    GenModel,
    GenOperation,
    GenPackage,
    PropertyMode,
    map_default_py_type,
)

_MODE = {
    "emf": GenerationMode.EMF,
    "decorator": GenerationMode.DECORATOR,
    "plain": GenerationMode.PLAIN,
}
_PROPERTY = {
    "editable": PropertyMode.EDITABLE,
    "readonly": PropertyMode.READONLY,
    "none": PropertyMode.NONE,
}
_GENMODEL_ANNOTATION_SOURCE = "http://www.eclipse.org/emf/2002/GenModel"


class GenConfigConverter:
    """Converts a :class:`GenConfig` into a :class:`GenModel`."""

    def convert(self, config: GenConfig) -> GenModel:
        gen_package = self._convert_package(config)
        defaults = config.class_defaults
        return GenModel(
            generation_mode=_MODE.get(config.generation.mode, GenerationMode.EMF),
            model_directory=config.generation.output_dir,
            root_extends_class=defaults.root_extends_class if defaults else "EObject",
            root_extends_interface=defaults.root_extends_interface if defaults else "EObject",
            generate_factory=config.package.generate_factory,
            generate_package=config.package.generate_package,
            generate_interfaces=defaults.generate_interface if defaults else True,
            generate_classes=defaults.generate_impl if defaults else True,
            gen_packages=[gen_package],
        )

    def _convert_package(self, config: GenConfig) -> GenPackage:
        e_package = config.ecore_package
        pkg_name = e_package.name or "model"
        class_override_map: dict[EClass, ClassOverride] = {
            o.ecore_class: o for o in config.class_overrides
        }

        gen_classes: list[GenClass] = []
        gen_enums: list[GenEnum] = []
        gen_data_types: list[GenDataType] = []
        for classifier in e_package.e_classifiers:
            if isinstance(classifier, EEnum):
                gen_enums.append(self._convert_enum(classifier))
            elif isinstance(classifier, EClass):
                gen_classes.append(
                    self._convert_class(classifier, config, class_override_map.get(classifier))
                )
            elif isinstance(classifier, EDataType):
                gen_data_types.append(self._convert_data_type(classifier))

        return GenPackage(
            ecore_package=e_package,
            prefix=config.package.prefix,
            base_package=config.package.base_package or "",
            file_extension=pkg_name.lower(),
            gen_classes=gen_classes,
            gen_enums=gen_enums,
            gen_data_types=gen_data_types,
        )

    def _convert_class(
        self, e_class: EClass, config: GenConfig, override: ClassOverride | None
    ) -> GenClass:
        feature_override_map: dict[EStructuralFeature, FeatureOverride] = {}
        if override is not None:
            feature_override_map = {fo.ecore_feature: fo for fo in override.feature_overrides}

        gen_features = [
            self._convert_feature(f, config, feature_override_map.get(f))
            for f in e_class.e_structural_features
        ]
        gen_operations = [self._convert_operation(op) for op in e_class.e_operations]

        defaults = config.class_defaults
        generate_interface = _first_not_none(
            override.generate_interface if override else None,
            defaults.generate_interface if defaults else None,
            True,
        )
        generate_impl = _first_not_none(
            override.generate_impl if override else None,
            defaults.generate_impl if defaults else None,
            True,
        )
        return GenClass(
            ecore_class=e_class,
            generate_interface=generate_interface,
            generate_impl=generate_impl,
            base_class=override.extends_class if override else None,
            gen_features=gen_features,
            gen_operations=gen_operations,
        )

    def _convert_feature(
        self, feature: EStructuralFeature, config: GenConfig, override: FeatureOverride | None
    ) -> GenFeature:
        notify = override.notify if override and override.notify is not None else None
        if notify is None and config.feature_defaults is not None:
            notify = config.feature_defaults.notify
        if notify is None:
            notify = config.generation.mode == "emf"

        prop: GenConfigPropertyMode | None = override.property if override else None
        if prop is None and config.feature_defaults is not None:
            prop = config.feature_defaults.property
        if prop is None:
            prop = "editable"

        is_containment = isinstance(feature, EReference) and feature.containment
        return GenFeature(
            ecore_feature=feature,
            notify=notify,
            property=_PROPERTY.get(prop, PropertyMode.EDITABLE),
            create_child=is_containment,
            getter_name=None,
            setter_name=None,
        )

    def _convert_operation(self, op: EOperation) -> GenOperation:
        body = self._read_body_annotation(op)
        return GenOperation(ecore_operation=op, generate_body=body is not None, body=body)

    def _read_body_annotation(self, op: EOperation) -> str | None:
        """Read the GenModel ``body`` annotation, mirroring Java EMF's convention
        of hand-authored method bodies stored as an ``eAnnotations`` detail."""
        annotation = op.get_e_annotation(_GENMODEL_ANNOTATION_SOURCE)
        if annotation is None:
            return None
        body = annotation.details.get_by_key("body")
        if body is None or not body.strip():
            return None
        return body

    def _convert_enum(self, e_enum: EEnum) -> GenEnum:
        return GenEnum(ecore_enum=e_enum, use_string_values=False)

    def _convert_data_type(self, data_type: EDataType) -> GenDataType:
        return GenDataType(
            ecore_data_type=data_type,
            py_type=map_default_py_type(data_type.name or "Any"),
        )


def _first_not_none(*values: bool | None) -> bool:
    for value in values:
        if value is not None:
            return value
    return False
