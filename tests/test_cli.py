"""Phase 6 — argparse CLI: ``init`` and ``generate``."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from emf_codegen.cli import main


def test_no_command_prints_help() -> None:
    assert main([]) == 0


def test_init_creates_genconfig(library_ecore_path: str, tmp_path: Path) -> None:
    out = tmp_path / "library.genconfig.xmi"
    rc = main([
        "init", "-m", library_ecore_path, "-o", str(out),
        "--mode", "plain", "--prefix", "Library",
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert 'mode="plain"' in text
    assert 'prefix="Library"' in text
    assert "http://example.org/library#/" in text


def test_init_then_generate_roundtrip(library_ecore_path: str, tmp_path: Path) -> None:
    config = tmp_path / "library.genconfig.xmi"
    generated = tmp_path / "gen"
    assert main([
        "init", "-m", library_ecore_path, "-o", str(config),
        "--mode", "plain", "--prefix", "Library",
        "--output-dir", str(generated),
    ]) == 0

    rc = main([
        "generate", "-m", library_ecore_path, "-c", str(config),
        "-o", str(generated / "genlib"), "-v",
    ])
    assert rc == 0

    sys.path.insert(0, str(generated))
    try:
        genlib = importlib.import_module("genlib")
        book = genlib.Book(title="Dune", pages=412)
        assert book.title == "Dune"
    finally:
        sys.path.remove(str(generated))
        for mod in list(sys.modules):
            if mod == "genlib" or mod.startswith("genlib."):
                del sys.modules[mod]
