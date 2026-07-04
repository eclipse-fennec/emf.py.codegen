"""Phase 3 — plain-mode generation produces importable, runnable Python."""

from __future__ import annotations

import importlib
import sys
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
def plain_files(library_ecore_path: str) -> dict[str, str]:
    lib = EcoreLoader().load(library_ecore_path)
    config = GenConfig(
        ecore_package=lib,
        generation=GenerationSettings(mode="plain", output_dir="./out"),
        package=PackageSettings(prefix="Library", base_package=""),
    )
    gen_model = GenConfigConverter().convert(config)
    result = CodeGenerator(gen_model).generate()
    assert result.success, [d.message for d in result.diagnostics if d.level == "error"]
    return {f.path: f.content for f in result.files}


def test_expected_files(plain_files: dict[str, str]) -> None:
    assert set(plain_files) >= {
        "book.py", "library.py", "person.py", "author.py", "employee.py",
        "book_category.py", "__init__.py",
    }


def test_enum_content(plain_files: dict[str, str]) -> None:
    enum = plain_files["book_category.py"]
    assert "class BookCategory(Enum):" in enum
    assert "FICTION = 0" in enum
    assert "BIOGRAPHY = 4" in enum


def test_class_content(plain_files: dict[str, str]) -> None:
    book = plain_files["book.py"]
    assert "@dataclass" in book
    assert "class Book:" in book
    assert 'title: str = ""' in book
    assert "pages: int = 0" in book
    assert "available: bool = True" in book
    assert "category: BookCategory = BookCategory.FICTION" in book
    # cross-class reference is a TYPE_CHECKING import + optional annotation
    assert "if TYPE_CHECKING:" in book
    assert "author: Author | None = None" in book


def test_inheritance(plain_files: dict[str, str]) -> None:
    author = plain_files["author.py"]
    assert "from .person import Person" in author
    assert "class Author(Person):" in author


def test_operation_body_from_genmodel_annotation(plain_files: dict[str, str]) -> None:
    person = plain_files["person.py"]
    assert "def getFullName(self) -> str:" in person
    assert 'return self.firstName + " " + self.lastName' in person
    assert "raise NotImplementedError" not in person


def test_operation_without_annotation_stays_a_stub(plain_files: dict[str, str]) -> None:
    employee = plain_files["employee.py"]
    assert "def calculateBonus(self, year: int) -> float:" in employee
    assert 'raise NotImplementedError("calculateBonus not implemented")' in employee


def test_generated_package_is_importable(
    library_ecore_path: str, tmp_path: Path
) -> None:
    lib = EcoreLoader().load(library_ecore_path)
    config = GenConfig(
        ecore_package=lib,
        generation=GenerationSettings(mode="plain", output_dir=str(tmp_path)),
        package=PackageSettings(prefix="Library", base_package=""),
    )
    gen_model = GenConfigConverter().convert(config)
    pkg_dir = tmp_path / "genlib"
    result = CodeGenerator(gen_model).generate()
    for file in result.files:
        file.write(str(pkg_dir))

    sys.path.insert(0, str(tmp_path))
    try:
        genlib = importlib.import_module("genlib")
        book = genlib.Book(title="1984", pages=328)
        assert book.title == "1984"
        assert book.pages == 328
        assert book.category is genlib.BookCategory.FICTION
        # Generated field names keep the Ecore feature names (as in the TS generator).
        author = genlib.Author(firstName="George", lastName="Orwell")
        assert author.firstName == "George"
        # inheritance: Author is a Person
        assert isinstance(author, genlib.Person)
        # body-annotated operation, inherited from Person
        assert author.getFullName() == "George Orwell"
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == "genlib" or mod.startswith("genlib."):
                del sys.modules[mod]
