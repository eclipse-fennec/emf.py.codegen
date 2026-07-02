"""Phase 1 — EcoreLoader loads library.ecore via EMFPy."""

from __future__ import annotations

from emf import EClass, EEnum, EReference

from emf_codegen.loader import EcoreLoader


def test_load_package_metadata(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    assert pkg.name == "library"
    assert pkg.ns_uri == "http://example.org/library"
    assert pkg.ns_prefix == "lib"


def test_classifiers_present(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    names = {c.name for c in pkg.e_classifiers}
    assert {"BookCategory", "Library", "Book", "Person", "Author", "Employee"} <= names


def test_enum_literals(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    category = pkg.get_e_classifier("BookCategory")
    assert isinstance(category, EEnum)
    assert [lit.name for lit in category.e_literals] == [
        "FICTION", "NON_FICTION", "SCIENCE", "HISTORY", "BIOGRAPHY",
    ]
    assert category.e_literals[2].value == 2


def test_inheritance(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    author = pkg.get_e_classifier("Author")
    person = pkg.get_e_classifier("Person")
    assert isinstance(author, EClass) and isinstance(person, EClass)
    assert person in author.e_super_types
    assert person.abstract is True
    # inherited attributes are visible
    assert author.get_e_structural_feature("firstName") is not None


def test_attribute_etype_resolved(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    book = pkg.get_e_classifier("Book")
    assert isinstance(book, EClass)
    title = book.get_e_structural_feature("title")
    assert title is not None
    assert title.e_type is not None and title.e_type.name == "EString"
    assert title.required is True  # lowerBound=1
    category = book.get_e_structural_feature("category")
    assert category is not None and category.e_type is pkg.get_e_classifier("BookCategory")


def test_reference_opposite_resolved(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    book = pkg.get_e_classifier("Book")
    library = pkg.get_e_classifier("Library")
    assert isinstance(book, EClass) and isinstance(library, EClass)
    books_ref = library.get_e_structural_feature("books")
    library_ref = book.get_e_structural_feature("library")
    assert isinstance(books_ref, EReference) and isinstance(library_ref, EReference)
    assert books_ref.containment is True
    assert books_ref.many is True
    assert books_ref.e_type is book
    # bidirectional opposite reconstructed on load
    assert books_ref.e_opposite is library_ref
    assert library_ref.e_opposite is books_ref


def test_load_errors_are_empty(library_ecore_path: str) -> None:
    loader = EcoreLoader()
    loader.load(library_ecore_path)  # raises if there were load errors
