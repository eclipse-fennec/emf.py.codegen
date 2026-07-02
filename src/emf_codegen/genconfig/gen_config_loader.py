"""GenConfigLoader — load a ``.genconfig.xmi`` into a :class:`GenConfig`.

Port of ``genconfig/GenConfigLoader.ts``, simpler in Python: EMFPy resolves the
``ecorePackage`` / ``ecoreClass`` / ``ecoreFeature`` references to real objects
during load (the user package is registered first), so most string-URI parsing
of the TS version is unnecessary; a proxy fallback covers the unresolved case.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from emf import (
    ECORE_NS_URI,
    URI,
    BasicResourceSet,
    EClass,
    EObject,
    EPackage,
    EStructuralFeature,
    XMIResource,
    get_ecore_package,
)

from emf_codegen.genconfig.gen_config import (
    ClassDefaults,
    ClassOverride,
    FeatureDefaults,
    FeatureOverride,
    GenConfig,
    GenConfigMode,
    GenConfigPropertyMode,
    GenerationSettings,
    PackageSettings,
    create_default_class_defaults,
    create_default_feature_defaults,
    create_default_generation_settings,
)
from emf_codegen.util.eobject_helper import get_feature_value

_GENCONFIG_ECORE = Path(__file__).resolve().parent / "genconfig.ecore"


class GenConfigLoader:
    """Loads GenConfig models, resolving references against registered packages."""

    def __init__(self) -> None:
        get_ecore_package()
        self._resource_set = BasicResourceSet()
        self._resource_set.get_package_registry().set(ECORE_NS_URI, get_ecore_package())
        self._ecore_packages: dict[str, EPackage] = {}
        self._load_genconfig_metamodel()

    def _load_genconfig_metamodel(self) -> None:
        content = _GENCONFIG_ECORE.read_text(encoding="utf-8")
        resource = XMIResource(URI.create_uri(str(_GENCONFIG_ECORE)))
        resource.set_resource_set(self._resource_set)
        resource.load_from_string(content)
        contents = resource.get_contents()
        if contents.size() > 0:
            pkg = contents.get(0)
            if isinstance(pkg, EPackage) and pkg.ns_uri:
                self._resource_set.get_package_registry().set(pkg.ns_uri, pkg)

    def register_package(self, e_package: EPackage) -> None:
        """Register a user EPackage so config references resolve to it."""
        if e_package.ns_uri:
            self._ecore_packages[e_package.ns_uri] = e_package
            self._resource_set.get_package_registry().set(e_package.ns_uri, e_package)

    def load(self, config_path: str) -> GenConfig:
        content = Path(config_path).read_text(encoding="utf-8")
        resource = XMIResource(URI.create_uri(config_path))
        resource.set_resource_set(self._resource_set)
        resource.load_from_string(content)
        contents = resource.get_contents()
        if contents.size() == 0:
            raise ValueError(f"No content found in {config_path}")
        return self._convert_to_gen_config(contents.get(0))

    # ----- conversion ------------------------------------------------------

    def _convert_to_gen_config(self, obj: EObject) -> GenConfig:
        ecore_package = self._resolve_package(get_feature_value(obj, "ecorePackage"))
        if ecore_package is None and self._ecore_packages:
            ecore_package = next(iter(self._ecore_packages.values()))
        if ecore_package is None:
            raise ValueError(
                "Could not resolve ecorePackage. Specify it in the GenConfig XMI or "
                "register a package via register_package() before loading."
            )

        generation = self._convert_generation_settings(get_feature_value(obj, "generation"))
        package = self._convert_package_settings(get_feature_value(obj, "package"))

        class_defaults_obj = get_feature_value(obj, "classDefaults")
        class_defaults = (
            self._convert_class_defaults(class_defaults_obj)
            if class_defaults_obj is not None
            else create_default_class_defaults()
        )
        feature_defaults_obj = get_feature_value(obj, "featureDefaults")
        feature_defaults = (
            self._convert_feature_defaults(feature_defaults_obj)
            if feature_defaults_obj is not None
            else create_default_feature_defaults(generation.mode)
        )
        overrides = self._convert_class_overrides(
            get_feature_value(obj, "classOverrides") or [], ecore_package
        )
        return GenConfig(
            ecore_package=ecore_package,
            generation=generation,
            package=package,
            class_defaults=class_defaults,
            feature_defaults=feature_defaults,
            class_overrides=overrides,
        )

    def _convert_generation_settings(self, obj: EObject | None) -> GenerationSettings:
        if obj is None:
            return create_default_generation_settings()
        raw_ext = get_feature_value(obj, "fileExtension")
        file_extension = ".py" if raw_ext in (None, "", ".ts") else raw_ext
        return GenerationSettings(
            mode=self._convert_mode(get_feature_value(obj, "mode")),
            output_dir=get_feature_value(obj, "outputDir") or "./generated",
            file_extension=file_extension,
            header_comment=get_feature_value(obj, "headerComment"),
        )

    def _convert_package_settings(self, obj: EObject | None) -> PackageSettings:
        if obj is None:
            raise ValueError("Package settings are required")
        return PackageSettings(
            prefix=get_feature_value(obj, "prefix") or "",
            base_package=get_feature_value(obj, "basePackage"),
            generate_factory=_as_bool(get_feature_value(obj, "generateFactory"), True),
            generate_package=_as_bool(get_feature_value(obj, "generatePackage"), True),
            generate_index=_as_bool(get_feature_value(obj, "generateIndex"), True),
        )

    def _convert_class_defaults(self, obj: EObject) -> ClassDefaults:
        return ClassDefaults(
            generate_interface=_as_bool(get_feature_value(obj, "generateInterface"), True),
            generate_impl=_as_bool(get_feature_value(obj, "generateImpl"), True),
            root_extends_class=get_feature_value(obj, "rootExtendsClass") or "EObject",
            root_extends_interface=get_feature_value(obj, "rootExtendsInterface") or "EObject",
        )

    def _convert_feature_defaults(self, obj: EObject) -> FeatureDefaults:
        return FeatureDefaults(
            notify=_as_bool(get_feature_value(obj, "notify"), True),
            property=self._convert_property_mode(get_feature_value(obj, "property")),
        )

    def _convert_class_overrides(
        self, objs: list[EObject], ecore_package: EPackage
    ) -> list[ClassOverride]:
        overrides: list[ClassOverride] = []
        for obj in objs:
            ecore_class = self._resolve_class(get_feature_value(obj, "ecoreClass"), ecore_package)
            if ecore_class is None:
                continue
            feature_overrides = self._convert_feature_overrides(
                get_feature_value(obj, "featureOverrides") or [], ecore_class
            )
            impls = get_feature_value(obj, "implementsInterfaces")
            overrides.append(
                ClassOverride(
                    ecore_class=ecore_class,
                    generate_interface=get_feature_value(obj, "generateInterface"),
                    generate_impl=get_feature_value(obj, "generateImpl"),
                    extends_class=get_feature_value(obj, "extendsClass"),
                    implements_interfaces=list(impls) if impls else None,
                    feature_overrides=feature_overrides,
                )
            )
        return overrides

    def _convert_feature_overrides(
        self, objs: list[EObject], ecore_class: EClass
    ) -> list[FeatureOverride]:
        overrides: list[FeatureOverride] = []
        for obj in objs:
            feature = self._resolve_feature(get_feature_value(obj, "ecoreFeature"), ecore_class)
            if feature is None:
                continue
            prop = get_feature_value(obj, "property")
            overrides.append(
                FeatureOverride(
                    ecore_feature=feature,
                    notify=get_feature_value(obj, "notify"),
                    property=self._convert_property_mode(prop) if prop is not None else None,
                    custom_getter=get_feature_value(obj, "customGetter"),
                    custom_setter=get_feature_value(obj, "customSetter"),
                )
            )
        return overrides

    def _convert_mode(self, value: Any) -> GenConfigMode:
        literal = _enum_literal(value)
        if literal in ("emf", "decorator", "plain"):
            return literal  # type: ignore[return-value]
        return "emf"

    def _convert_property_mode(self, value: Any) -> GenConfigPropertyMode:
        literal = _enum_literal(value)
        if literal in ("editable", "readonly", "none"):
            return literal  # type: ignore[return-value]
        return "editable"

    # ----- reference resolution (EMFPy usually resolves; proxy fallback) ---

    def _resolve_package(self, ref: Any) -> EPackage | None:
        if isinstance(ref, EPackage):
            return ref
        uri = _proxy_uri(ref)
        if uri is not None:
            ns_uri = re.sub(r"#/?.*$", "", uri)
            return self._ecore_packages.get(ns_uri)
        return None

    def _resolve_class(self, ref: Any, default_package: EPackage) -> EClass | None:
        if isinstance(ref, EClass):
            return ref
        uri = _proxy_uri(ref)
        if uri is None:
            return None
        match = re.match(r"^(.+)#//(.+)$", uri)
        if not match:
            return None
        ns_uri, class_name = match.group(1), match.group(2)
        pkg = self._ecore_packages.get(ns_uri, default_package)
        classifier = pkg.get_e_classifier(class_name)
        return classifier if isinstance(classifier, EClass) else None

    def _resolve_feature(self, ref: Any, default_class: EClass) -> EStructuralFeature | None:
        if isinstance(ref, EStructuralFeature):
            return ref
        uri = _proxy_uri(ref)
        if uri is None:
            return None
        match = re.match(r"^(.+)#//(.+)/(.+)$", uri)
        if not match:
            return None
        ns_uri, class_name, feature_name = match.group(1), match.group(2), match.group(3)
        pkg = self._ecore_packages.get(ns_uri)
        eclass = pkg.get_e_classifier(class_name) if pkg is not None else None
        if not isinstance(eclass, EClass):
            eclass = default_class
        return eclass.get_e_structural_feature(feature_name)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value == "true"
    return bool(value)


def _enum_literal(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    literal = getattr(value, "literal", None)
    if literal:
        return literal  # type: ignore[no-any-return]
    name = getattr(value, "name", None)
    return name if isinstance(name, str) else None


def _proxy_uri(ref: Any) -> str | None:
    is_proxy = getattr(ref, "e_is_proxy", None)
    if callable(is_proxy) and is_proxy():
        uri = ref.e_proxy_uri()
        return str(uri) if uri is not None else None
    return str(ref) if isinstance(ref, str) else None
