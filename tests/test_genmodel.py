"""Phase 1 — internal generation model + default construction."""

from __future__ import annotations

from emf import EClass, EEnum

from emf_codegen.genmodel import (
    GenerationMode,
    create_default_gen_class,
    create_default_gen_data_type,
    create_default_gen_enum,
    create_default_gen_model,
    create_default_gen_package,
    map_default_py_type,
)
from emf_codegen.loader import EcoreLoader


def test_default_gen_model() -> None:
    gm = create_default_gen_model()
    assert gm.generation_mode is GenerationMode.DECORATOR
    assert gm.generate_interfaces is True
    assert gm.root_extends_class == "EObject"
    assert gm.gen_packages == []


def test_default_gen_package(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    gp = create_default_gen_package(pkg)
    assert gp.ecore_package is pkg
    assert gp.prefix == "Library"  # capitalized name
    assert gp.file_extension == "library"
    assert gp.class_package_suffix == "impl"


def test_default_gen_class_and_feature(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    book = pkg.get_e_classifier("Book")
    assert isinstance(book, EClass)
    gc = create_default_gen_class(book)
    assert gc.ecore_class is book
    assert gc.generate_interface and gc.generate_impl
    assert gc.dynamic is False


def test_default_gen_enum(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    category = pkg.get_e_classifier("BookCategory")
    assert isinstance(category, EEnum)
    ge = create_default_gen_enum(category)
    assert ge.ecore_enum is category
    assert ge.use_string_values is True


def test_map_default_py_type() -> None:
    assert map_default_py_type("EString") == "str"
    assert map_default_py_type("EBoolean") == "bool"
    assert map_default_py_type("EInt") == "int"
    assert map_default_py_type("ELong") == "int"
    assert map_default_py_type("EDouble") == "float"
    assert map_default_py_type("EDate") == "datetime"
    assert map_default_py_type("EJavaObject") == "Any"
    assert map_default_py_type("CustomType") == "CustomType"


def test_default_gen_data_type(library_ecore_path: str) -> None:
    pkg = EcoreLoader().load(library_ecore_path)
    # EString resolves via the Ecore registry; grab it from a feature's type.
    book = pkg.get_e_classifier("Book")
    assert isinstance(book, EClass)
    estring = book.get_e_structural_feature("title").e_type  # type: ignore[union-attr]
    gdt = create_default_gen_data_type(estring)
    assert gdt.py_type == "str"
    assert gdt.ecore_data_type is estring
