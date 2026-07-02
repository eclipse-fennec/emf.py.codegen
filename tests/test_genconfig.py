"""Phase 2 — load library.genconfig.xmi and convert to a GenModel."""

from __future__ import annotations

from pathlib import Path

import pytest

from emf_codegen.genconfig import GenConfig, GenConfigConverter, GenConfigLoader
from emf_codegen.genmodel import GenerationMode, PropertyMode
from emf_codegen.loader import EcoreLoader

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "model"
GENCONFIG = str(EXAMPLES / "library.genconfig.xmi")


@pytest.fixture
def config(library_ecore_path: str) -> GenConfig:
    lib = EcoreLoader().load(library_ecore_path)
    loader = GenConfigLoader()
    loader.register_package(lib)
    return loader.load(GENCONFIG)


def test_generation_settings(config: GenConfig) -> None:
    assert config.generation.mode == "emf"
    assert config.generation.output_dir == "./generated"


def test_package_settings(config: GenConfig) -> None:
    assert config.package.prefix == "Library"
    assert config.package.base_package == "org.example"
    assert config.package.generate_factory is True
    assert config.package.generate_index is True


def test_ecore_package_resolved(config: GenConfig) -> None:
    assert config.ecore_package.ns_uri == "http://example.org/library"


def test_class_defaults(config: GenConfig) -> None:
    assert config.class_defaults is not None
    assert config.class_defaults.generate_interface is True
    assert config.class_defaults.root_extends_class == "BasicEObject"


def test_class_and_feature_overrides(config: GenConfig) -> None:
    by_class = {o.ecore_class.name: o for o in config.class_overrides}
    assert set(by_class) == {"Book", "Author", "Employee"}
    book = by_class["Book"]
    fos = {f.ecore_feature.name: f for f in book.feature_overrides}
    assert fos["author"].notify is False
    assert fos["library"].notify is False
    assert fos["library"].property == "readonly"


class TestConverter:
    def test_to_gen_model(self, config: GenConfig) -> None:
        gm = GenConfigConverter().convert(config)
        assert gm.generation_mode is GenerationMode.EMF
        assert gm.model_directory == "./generated"
        assert len(gm.gen_packages) == 1

    def test_classifiers_partitioned(self, config: GenConfig) -> None:
        gp = GenConfigConverter().convert(config).gen_packages[0]
        assert {gc.ecore_class.name for gc in gp.gen_classes} == {
            "Library", "Book", "Person", "Author", "Employee",
        }
        assert {ge.ecore_enum.name for ge in gp.gen_enums} == {"BookCategory"}
        assert gp.prefix == "Library"

    def test_feature_override_applied(self, config: GenConfig) -> None:
        gp = GenConfigConverter().convert(config).gen_packages[0]
        book = next(gc for gc in gp.gen_classes if gc.ecore_class.name == "Book")
        features = {f.ecore_feature.name: f for f in book.gen_features}
        assert features["author"].notify is False
        assert features["library"].property is PropertyMode.READONLY
        # containment refs get create_child
        assert features["author"].create_child is False

    def test_create_child_for_containment(self, config: GenConfig) -> None:
        gp = GenConfigConverter().convert(config).gen_packages[0]
        library = next(gc for gc in gp.gen_classes if gc.ecore_class.name == "Library")
        books = next(f for f in library.gen_features if f.ecore_feature.name == "books")
        assert books.create_child is True
