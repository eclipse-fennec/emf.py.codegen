"""Phase 4 — emf mode generates concrete, typed EObject subclasses."""

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


def _gen(library_ecore_path: str, output_dir: str) -> CodeGenerator:
    lib = EcoreLoader().load(library_ecore_path)
    config = GenConfig(
        ecore_package=lib,
        generation=GenerationSettings(mode="emf", output_dir=output_dir),
        package=PackageSettings(prefix="Library", base_package=""),
    )
    return CodeGenerator(GenConfigConverter().convert(config))


@pytest.fixture
def emf_files(library_ecore_path: str) -> dict[str, str]:
    result = _gen(library_ecore_path, "./out").generate()
    assert result.success, [d.message for d in result.diagnostics if d.level == "error"]
    return {f.path: f.content for f in result.files if f.generated}


def test_expected_files(emf_files: dict[str, str]) -> None:
    assert set(emf_files) >= {
        "book.py", "library.py", "person.py", "author.py", "employee.py",
        "book_category.py", "library_package.py", "library_factory.py", "__init__.py",
    }


def test_class_is_typed_eobject_subclass(emf_files: dict[str, str]) -> None:
    book = emf_files["book.py"]
    assert "class Book(EObject):" in book
    assert "self._eclass = BOOK" in book
    assert "def title(self) -> str:" in book
    assert 'return cast("str", self.e_get(BOOK__TITLE))' in book
    assert "self.e_set(BOOK__TITLE, value)" in book
    # category is exposed as the Python enum type
    assert "def category(self) -> BookCategory:" in book


def test_readonly_feature_has_no_setter(
    library_ecore_path: str, library_genconfig_path: str
) -> None:
    # The example genconfig overrides Book.library to property="readonly".
    from emf_codegen import generate_in_memory

    result = generate_in_memory(library_ecore_path, library_genconfig_path)
    book = next(f.content for f in result.files if f.path.endswith("book.py"))
    assert "def library(self) -> Library | None:" in book
    assert "@library.setter" not in book


def test_inheritance(emf_files: dict[str, str]) -> None:
    assert "class Author(Person):" in emf_files["author.py"]
    assert "from .person import Person" in emf_files["author.py"]
    # many-valued reference is exposed as a live EList, no setter
    assert "def books(self) -> EList[Book]:" in emf_files["author.py"]


def test_operation_body_from_genmodel_annotation(emf_files: dict[str, str]) -> None:
    person = emf_files["person.py"]
    assert "def getFullName(self) -> str:" in person
    assert 'return self.firstName + " " + self.lastName' in person
    assert "raise NotImplementedError" not in person


def test_operation_without_annotation_stays_a_stub(emf_files: dict[str, str]) -> None:
    employee = emf_files["employee.py"]
    assert "def calculateBonus(self) -> float:" in employee
    assert 'raise NotImplementedError("calculateBonus not implemented")' in employee


def test_package_module_wires_metamodel(emf_files: dict[str, str]) -> None:
    pkg = emf_files["library_package.py"]
    assert 'BOOK = EClass("Book", abstract=False)' in pkg
    assert 'PERSON = EClass("Person", abstract=True)' in pkg
    assert "BOOK__AUTHOR.e_opposite = AUTHOR__BOOKS" in pkg
    assert 'BOOK__PAGES.default_value_literal = "0"' in pkg
    assert "_lit.instance = BookCategory.FICTION" in pkg
    assert "PackageRegistry.INSTANCE.register_package(PACKAGE)" in pkg


def test_generated_package_runs(library_ecore_path: str, tmp_path: Path) -> None:
    for file in _gen(library_ecore_path, str(tmp_path)).generate().files:
        file.write(str(tmp_path / "emflib"))

    sys.path.insert(0, str(tmp_path))
    try:
        emflib = importlib.import_module("emflib")
        book = emflib.Book()
        book.title = "1984"
        assert book.title == "1984"
        # default value literals parse through the data type
        assert book.pages == 0
        assert book.available is True
        assert book.category is emflib.BookCategory.FICTION

        # inheritance + inherited attribute
        author = emflib.Author()
        author.firstName = "George"
        author.lastName = "Orwell"
        assert author.firstName == "George"
        assert isinstance(author, emflib.Person)
        # body-annotated operation, inherited from Person, backed by e_get properties
        assert author.getFullName() == "George Orwell"

        # bidirectional (non-containment) opposite maintenance via e_set
        book.author = author
        assert book in list(author.books)

        # containment + readonly container reference
        library = emflib.Library()
        library.books.add(book)
        assert book.e_container() is library
        assert book.library is library

        # factory
        assert type(emflib.LibraryFactory().create_book()).__name__ == "Book"
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == "emflib" or mod.startswith("emflib."):
                del sys.modules[mod]
