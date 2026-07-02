# emf-codegen — Python code generator for Ecore

A Python code generator for [Ecore](https://eclipse.dev/modeling/emf/) models, built on
[**EMFPy**](../EMFPy-core) — the Python port of EMF/Ecore. It is the Python equivalent of the
TypeScript `@emfts/codegen`.

> Status: **complete** (Phases 1–4, 6–8; Phase 5 intentionally out of scope).
> See [`PLAN.md`](./PLAN.md) for the roadmap.

## What it does

- Loads an `.ecore` model (via EMFPy's XMI reader) plus a `.genconfig.xmi` configuration.
- Builds an internal generation model (`GenModel` / `GenPackage` / `GenClass` / …).
- Emits **Python** source in one of three modes:
  - **plain** — dataclass-style Python classes (no EMF runtime dependency),
  - **decorator** — dataclasses carrying Ecore metadata (`ECLASS_URI` class var +
    `field(metadata={"kind", "type", "many"})`),
  - **emf** — concrete, typed `EObject` subclasses (one per `EClass`) whose `@property`
    accessors delegate to `e_get`/`e_set`, plus a `<prefix>_package` module holding the
    `EPackage` and class/feature *literals*, a factory, and an `__init__` barrel.
- A CLI (`emfpy-codegen generate …` / `init …`) for build pipelines.

## Generation modes

| Mode | Output | Runtime dependency | Use when |
|---|---|---|---|
| `plain` | `@dataclass` per class + `Enum` | none | plain data holders, no EMF semantics |
| `decorator` | `@dataclass` + metadata + `ECLASS_URI` | none (metadata is inert) | data holders that retain Ecore provenance |
| `emf` | typed `EObject` subclass per class + package/factory/barrel | `emf` | full EMF semantics (reflection, opposites, containment) with a typed class API |

### Python adaptations vs. the TypeScript original

- **decorator:** EMFPy has no per-field decorator framework, so the TS `@ModelClass` /
  `@Attribute` / `@Reference` decorators become an `ECLASS_URI` class variable plus
  `dataclasses.field(metadata=…)`, reachable via `dataclasses.fields()`.
- **emf:** like the TS original, one concrete class per `EClass`. The TS impl stores values
  in private fields and reimplements the reflective `eGet`/`eSet` switch; the Python classes
  instead back every typed `@property` with `self.e_get`/`self.e_set` on the package's feature
  literals, so the EMFPy runtime maintains opposites, containment and container references for
  free. Generated classes are themselves `mypy --strict` clean.

## Usage

```bash
# Generate from an existing model + config
emfpy-codegen generate -m examples/model/library.ecore \
    -c examples/model/library.genconfig.xmi -o generated -v

# Bootstrap a .genconfig.xmi for a model
emfpy-codegen init -m examples/model/library.ecore --mode emf --prefix Library
```

Programmatic API:

```python
from emf_codegen import generate, generate_in_memory

result = generate("model/library.ecore", "model/library.genconfig.xmi", output_dir="out")
for diag in result.diagnostics:
    print(diag.level, diag.message)
```

### Generated emf-mode example

```python
from org.example import Book, Author, Library, BookCategory   # generated classes

book = Book()
book.title = "Neuromancer"
print(book.available)              # True  (default literal "true" parsed)
print(book.category)               # BookCategory.FICTION

author = Author()
book.author = author               # bidirectional opposite is maintained …
assert book in list(author.books)  # … so author.books now contains the book

library = Library()
library.books.add(book)            # containment
assert book.library is library     # readonly container reference derives from it
```

A ready-made example is generated under [`examples/generated/`](./examples/generated).

## Relationship to the TypeScript original

| `@emfts/codegen` | `emf-codegen` |
|---|---|
| generates TypeScript | generates Python |
| `@emfts/core` runtime | `emf` (EMFPy) runtime |
| EJS templates | Jinja2 templates |
| `commander` CLI | `argparse` CLI |
| `sax` for XMI | EMFPy `XMIResource` (stdlib `xml.sax`) |
| `@ModelClass`/`@Attribute` decorators | `ECLASS_URI` + `field(metadata=…)` |
| per-class `BasicEObject` subclass + field-backed reflective `eGet`/`eSet` | per-class `EObject` subclass with `@property` → `e_get`/`e_set` |
| service-interface + REST-client generators | out of scope |

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ../EMFPy-core   # the EMFPy runtime (provides the `emf` package)
pip install -e ".[dev]"
pytest && ruff check . && mypy
```

## License

Eclipse Public License 2.0 (EPL-2.0).
