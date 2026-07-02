"""Smoke test: the package skeleton imports, the EMFPy runtime is available,
and the CLI entry point is wired."""

from __future__ import annotations

import importlib

import emf_codegen
from emf_codegen.cli import main


def test_package_has_version() -> None:
    assert isinstance(emf_codegen.__version__, str)
    assert emf_codegen.__version__


def test_emfpy_runtime_available() -> None:
    # emf-codegen builds on the EMFPy runtime.
    emf = importlib.import_module("emf")
    assert hasattr(emf, "XMIResource")
    assert hasattr(emf, "EPackage")


def test_planned_subpackages_exist() -> None:
    for sub in (
        "emf_codegen.loader",
        "emf_codegen.genmodel",
        "emf_codegen.genconfig",
        "emf_codegen.generator",
        "emf_codegen.generator.modes",
        "emf_codegen.cli",
    ):
        assert importlib.import_module(sub) is not None


def test_cli_no_args_prints_help() -> None:
    assert main([]) == 0
