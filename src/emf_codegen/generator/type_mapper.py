"""TypeMapper — Ecore types to **Python** type annotations.

Port of ``generator/TypeMapper.ts`` (which targets TypeScript). Also computes
sensible Python default values for fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from emf import EClass, EEnum, EReference

if TYPE_CHECKING:
    from emf import EClassifier, EStructuralFeature

#: Ecore data-type name -> Python type annotation.
PRIMITIVE_MAP: dict[str, str] = {
    "EString": "str", "EChar": "str", "ECharacterObject": "str",
    "EBoolean": "bool", "EBooleanObject": "bool",
    "EInt": "int", "EIntegerObject": "int", "EByte": "int", "EByteObject": "int",
    "EShort": "int", "EShortObject": "int", "ELong": "int", "ELongObject": "int",
    "EBigInteger": "int",
    "EFloat": "float", "EFloatObject": "float", "EDouble": "float",
    "EDoubleObject": "float", "EBigDecimal": "float",
    "EDate": "datetime",
    "EJavaObject": "Any", "EJavaClass": "Any", "EFeatureMapEntry": "Any",
}

_PY_DEFAULT = {"str": '""', "bool": "False", "int": "0", "float": "0.0"}


class TypeMapper:
    """Maps Ecore classifiers/features to Python types and default values."""

    def __init__(self) -> None:
        self._custom: dict[str, str] = dict(PRIMITIVE_MAP)

    def add_mapping(self, ecore_name: str, py_type: str) -> None:
        self._custom[ecore_name] = py_type

    def map_classifier(self, classifier: EClassifier | None) -> str:
        if classifier is None:
            return "Any"
        name = classifier.name
        if not name:
            return "Any"
        return self._custom.get(name, name)

    def map_feature_base_type(self, feature: EStructuralFeature) -> str:
        return self.map_classifier(feature.e_type)

    def map_feature(self, feature: EStructuralFeature) -> str:
        base = self.map_feature_base_type(feature)
        if feature.many:
            return f"list[{base}]"
        return base

    def is_enum(self, classifier: EClassifier | None) -> bool:
        return isinstance(classifier, EEnum)

    def is_eclass(self, classifier: EClassifier | None) -> bool:
        return isinstance(classifier, EClass)

    def is_reference(self, feature: EStructuralFeature) -> bool:
        return isinstance(feature, EReference)

    def get_default_value(self, feature: EStructuralFeature) -> str:
        """A Python default-value expression for ``feature`` (always defined).

        Every generated field carries a default so dataclass field ordering is
        never violated across inheritance.
        """
        if feature.many:
            return "field(default_factory=list)"

        literal = feature.default_value_literal
        if literal is not None:
            return self._convert_literal(feature, literal)

        if feature.lower_bound == 0:
            return "None"

        return _PY_DEFAULT.get(self.map_feature_base_type(feature), "None")

    def _convert_literal(self, feature: EStructuralFeature, literal: str) -> str:
        base = self.map_feature_base_type(feature)
        if base == "str":
            return f'"{literal}"'
        if base == "bool":
            return "True" if literal.lower() == "true" else "False"
        if base in ("int", "float"):
            return literal
        if base == "datetime":
            return f'datetime.fromisoformat("{literal}")'
        e_type = feature.e_type
        if isinstance(e_type, EEnum):
            return f"{e_type.name}.{literal}"
        return f'"{literal}"'
