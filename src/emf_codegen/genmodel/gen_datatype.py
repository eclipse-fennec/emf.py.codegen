"""GenDataType (port of ``genmodel/GenDataType.ts``).

Maps Ecore data types to **Python** types (the TS original maps to TS types).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emf import EDataType

_INT_TYPES = {
    "EInt", "EIntegerObject", "EByte", "EByteObject", "ELong", "ELongObject",
    "EShort", "EShortObject", "EBigInteger",
}
_FLOAT_TYPES = {"EFloat", "EFloatObject", "EDouble", "EDoubleObject", "EBigDecimal"}


def map_default_py_type(type_name: str) -> str:
    """Map an Ecore data-type name to a default Python type annotation."""
    if type_name in ("EString", "EChar", "ECharacterObject"):
        return "str"
    if type_name in ("EBoolean", "EBooleanObject"):
        return "bool"
    if type_name in _INT_TYPES:
        return "int"
    if type_name in _FLOAT_TYPES:
        return "float"
    if type_name == "EDate":
        return "datetime"
    if type_name in ("EJavaObject", "EJavaClass"):
        return "Any"
    return type_name


@dataclass
class GenDataType:
    """Generation configuration for an EDataType."""

    ecore_data_type: EDataType
    py_type: str
    serialize_function: str | None = None
    deserialize_function: str | None = None


def create_default_gen_data_type(data_type: EDataType) -> GenDataType:
    return GenDataType(
        ecore_data_type=data_type,
        py_type=map_default_py_type(data_type.name or "Any"),
    )
