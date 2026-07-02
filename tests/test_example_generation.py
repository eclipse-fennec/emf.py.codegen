"""Phase 7 — end-to-end generation from the bundled example model + genconfig.

Mirrors the TS ``generate:example`` smoke test: load the real ``library.ecore``
and ``library.genconfig.xmi`` (mode ``emf``, with class/feature overrides),
generate, and exercise the generated dynamic-EMF package.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from emf_codegen import generate, generate_in_memory


def test_example_generates_successfully(
    library_ecore_path: str, library_genconfig_path: str
) -> None:
    result = generate_in_memory(library_ecore_path, library_genconfig_path)
    assert result.success, [d.message for d in result.diagnostics if d.level == "error"]
    paths = {f.path for f in result.files if f.generated}
    # mode=emf, basePackage "org.example" → class-per-file + package/factory/barrel.
    assert "org/example/book.py" in paths
    assert "org/example/library_package.py" in paths
    assert "org/example/__init__.py" in paths
    assert all(p.endswith(".py") for p in paths)


def test_example_package_runs(
    library_ecore_path: str, library_genconfig_path: str, tmp_path: Path
) -> None:
    result = generate(
        library_ecore_path,
        library_genconfig_path,
        output_dir=str(tmp_path),
    )
    assert result.success

    # basePackage org.example → org/example/__init__.py; make it importable.
    sys.path.insert(0, str(tmp_path))
    (tmp_path / "org" / "__init__.py").touch()
    try:
        example = importlib.import_module("org.example")
        book = example.Book()
        book.title = "Neuromancer"
        assert book.title == "Neuromancer"
        assert book.available is True  # default literal "true" parsed

        author = example.Author()
        book.author = author
        assert book in list(author.books)
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == "org" or mod.startswith("org."):
                del sys.modules[mod]
