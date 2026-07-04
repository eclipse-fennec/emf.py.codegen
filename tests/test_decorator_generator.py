"""Phase 4 — decorator-mode generation produces metadata-annotated dataclasses."""

from __future__ import annotations

import importlib
import sys
from dataclasses import fields
from pathlib import Path

import pytest

from emf_codegen.genconfig import (
    GenConfig,
    GenConfigConverter,
    GenerationSettings,
    PackageSettings,
)
from emf_codegen.generator import CodeGenerator
from emf_codegen.loader import EcoreLoader


@pytest.fixture
def decorator_files(library_ecore_path: str) -> dict[str, str]:
    lib = EcoreLoader().load(library_ecore_path)
    config = GenConfig(
        ecore_package=lib,
        generation=GenerationSettings(mode="decorator", output_dir="./out"),
        package=PackageSettings(prefix="Library", base_package=""),
    )
    gen_model = GenConfigConverter().convert(config)
    result = CodeGenerator(gen_model).generate()
    assert result.success, [d.message for d in result.diagnostics if d.level == "error"]
    return {f.path: f.content for f in result.files if f.generated}


def test_expected_files(decorator_files: dict[str, str]) -> None:
    assert set(decorator_files) >= {
        "book.py", "library.py", "author.py", "book_category.py", "__init__.py",
    }


def test_class_has_eclass_uri_and_metadata(decorator_files: dict[str, str]) -> None:
    book = decorator_files["book.py"]
    assert "ECLASS_URI: ClassVar[str] =" in book
    assert "#//Book" in book
    assert 'field(default=""' in book
    assert '"kind": "attribute"' in book
    assert '"kind": "enum"' in book
    # cross-class reference carries reference metadata
    assert '"kind": "reference"' in book


def test_operation_body_from_genmodel_annotation(decorator_files: dict[str, str]) -> None:
    person = decorator_files["person.py"]
    assert "def getFullName(self) -> str:" in person
    assert 'return self.firstName + " " + self.lastName' in person
    assert "raise NotImplementedError" not in person


def test_operation_without_annotation_stays_a_stub(decorator_files: dict[str, str]) -> None:
    employee = decorator_files["employee.py"]
    assert "def calculateBonus(self, year: int) -> float:" in employee
    assert 'raise NotImplementedError("calculateBonus not implemented")' in employee


def test_generated_package_is_importable(
    library_ecore_path: str, tmp_path: Path
) -> None:
    lib = EcoreLoader().load(library_ecore_path)
    config = GenConfig(
        ecore_package=lib,
        generation=GenerationSettings(mode="decorator", output_dir=str(tmp_path)),
        package=PackageSettings(prefix="Library", base_package=""),
    )
    gen_model = GenConfigConverter().convert(config)
    pkg_dir = tmp_path / "declib"
    for file in CodeGenerator(gen_model).generate().files:
        file.write(str(pkg_dir))

    sys.path.insert(0, str(tmp_path))
    try:
        declib = importlib.import_module("declib")
        book = declib.Book(title="1984", pages=328)
        assert book.title == "1984"
        assert book.ECLASS_URI.endswith("#//Book")
        # metadata is reachable via dataclasses.fields
        meta = {f.name: f.metadata for f in fields(book)}
        assert meta["title"]["kind"] == "attribute"
        assert meta["category"]["kind"] == "enum"

        author = declib.Author(firstName="George", lastName="Orwell")
        assert author.getFullName() == "George Orwell"
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == "declib" or mod.startswith("declib."):
                del sys.modules[mod]
