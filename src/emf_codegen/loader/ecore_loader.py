"""EcoreLoader — load ``.ecore`` models via EMFPy (port of ``loader/EcoreLoader.ts``).

Synchronous (the TS version is async). Loaded packages are registered in the
shared resource set's package registry so cross-references resolve.
"""

from __future__ import annotations

from pathlib import Path

from emf import (
    ECORE_NS_URI,
    URI,
    BasicResourceSet,
    EPackage,
    XMIResource,
    get_ecore_package,
)


class EcoreLoader:
    """Loads Ecore models, sharing one resource set across calls."""

    def __init__(self) -> None:
        get_ecore_package()  # ensure the Ecore metamodel is initialized + registered
        self._resource_set = BasicResourceSet()
        self._resource_set.get_package_registry().set(ECORE_NS_URI, get_ecore_package())
        self._loaded_packages: dict[str, EPackage] = {}

    @property
    def resource_set(self) -> BasicResourceSet:
        return self._resource_set

    def load(self, ecore_path: str) -> EPackage:
        """Load the root :class:`EPackage` from ``ecore_path``."""
        content = Path(ecore_path).read_text(encoding="utf-8")
        resource = XMIResource(URI.create_uri(ecore_path))
        resource.set_resource_set(self._resource_set)
        resource.load_from_string(content)

        errors = resource.get_errors()
        if errors:
            joined = ", ".join(e.get("message", str(e)) for e in errors)
            raise ValueError(f"Errors loading Ecore '{ecore_path}': {joined}")

        contents = resource.get_contents()
        if contents.size() == 0:
            raise ValueError(f"No content found in {ecore_path}")
        root = contents.get(0)
        if not isinstance(root, EPackage):
            raise ValueError(f"Root element is not an EPackage in {ecore_path}")

        ns_uri = root.ns_uri
        if ns_uri:
            self._loaded_packages[ns_uri] = root
            self._resource_set.get_package_registry().set(ns_uri, root)
        return root

    def load_all(self, ecore_paths: list[str]) -> dict[str, EPackage]:
        for path in ecore_paths:
            self.load(path)
        return dict(self._loaded_packages)

    def get_package(self, ns_uri: str) -> EPackage | None:
        return self._loaded_packages.get(ns_uri)

    def get_all_packages(self) -> dict[str, EPackage]:
        return dict(self._loaded_packages)
