"""Reflective accessors over EMFPy EObjects (port of ``util/EObjectHelper.ts``).

The TS version duck-types because it reads dynamic objects; EMFPy gives real
metamodel instances, so most helpers are thin wrappers. ``get_feature_value`` is
the workhorse for reading dynamically-loaded models (e.g. ``.genconfig.xmi``).
"""

from __future__ import annotations

from typing import Any

_MISSING = object()


def get_feature_value(obj: Any, feature_name: str) -> Any:
    """Reflectively read ``feature_name`` from ``obj`` (or None)."""
    if obj is None:
        return None
    eclass = obj.e_class()
    if eclass is None:
        return None
    feature = eclass.get_e_structural_feature(feature_name)
    if feature is None:
        return None
    return obj.e_get(feature)


def get_name(obj: Any) -> str | None:
    """The element's name via the ``name`` property or the ``name`` feature."""
    if obj is None:
        return None
    name = getattr(obj, "name", _MISSING)
    if name is not _MISSING:
        return name if isinstance(name, str) else None
    value = get_feature_value(obj, "name")
    return value if isinstance(value, str) else None
