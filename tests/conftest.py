"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "model"


@pytest.fixture
def library_ecore_path() -> str:
    return str(EXAMPLES / "library.ecore")


@pytest.fixture
def library_genconfig_path() -> str:
    return str(EXAMPLES / "library.genconfig.xmi")
