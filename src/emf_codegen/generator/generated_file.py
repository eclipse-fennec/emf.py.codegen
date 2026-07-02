"""GeneratedFile (port of ``generator/GeneratedFile.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedFile:
    """A generated file: a path relative to the output directory plus its content."""

    path: str
    content: str
    generated: bool = True

    def write(self, output_dir: str) -> None:
        if not self.generated:
            return
        full = Path(output_dir) / self.path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(self.content, encoding="utf-8")
