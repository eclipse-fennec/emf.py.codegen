# emf-codegen — Implementierungsplan

Python-Portierung von `EMFTs/emfts-codegen` (TS-Code-Generator für Ecore). Das
Python-Äquivalent generiert **Python**-Code auf Basis der EMFPy-Runtime (`emf`).

## Eckdaten / Entscheidungen

| Thema | Entscheidung |
|---|---|
| Quelle der Wahrheit | TS `emfts-codegen` für Struktur & Verhalten, EMF-Semantik bei Bedarf |
| Zielsprache der Generierung | **Python** (TS-Original generiert TS) |
| Runtime des generierten Codes | `emf` (EMFPy) |
| Templating | **Jinja2** (statt EJS) |
| CLI | stdlib **argparse** (statt commander), Entry-Point `emfpy-codegen` |
| `.ecore`/`.genconfig.xmi` laden | EMFPy `XMIResource` (stdlib `xml.sax`) |
| Naming | pythonic `snake_case`; EMF/Gen-Klassennamen bleiben (`GenModel`, `GenClass`, …) |
| Python | 3.11+ |

## Paket-Layout (Spiegel von `src/`)

```
src/emf_codegen/
  __init__.py            # generate() / generate_in_memory() (Spiegel von index.ts)
  loader/ecore_loader.py # .ecore via EMFPy laden
  genmodel/              # internes Generierungsmodell
    generation_mode.py   # GenerationMode, PropertyMode
    gen_model.py, gen_package.py, gen_class.py, gen_feature.py,
    gen_enum.py, gen_datatype.py, gen_operation.py
  genconfig/
    gen_config.py        # Konfig-Datentypen (Settings/Defaults/Overrides)
    gen_config_loader.py # .genconfig.xmi laden
    gen_config_converter.py  # GenConfig → GenModel
  generator/
    type_mapper.py       # Ecore-Typ → Python-Typ
    import_resolver.py, generator_context.py, generated_file.py,
    generator_options.py, code_generator.py
    service_interface_generator.py, rest_client_generator.py
    modes/{base_generator.py, plain_generator.py, emf_generator.py, decorator_generator.py}
  templates/{plain,emf,decorator}/*.jinja   # erzeugen Python-Quelltext
  cli/__init__.py        # argparse-Dispatcher (main)
  cli/commands/{generate.py, init.py, generate_rest_client.py, generate_service_interfaces.py}
  util/{string_utils.py, eobject_helper.py}
examples/model/          # library.ecore + library.genconfig.xmi
tests/                   # pytest
```

## Generierungsmodi (erzeugen Python statt TS)

- **plain** — schlanke Python-Klassen (dataclass-artig), keine Runtime-Abhängigkeit.
- **emf** — Klassen auf EMFPy-Runtime (EObject-Subklassen, EPackage + Factory, reflektiv).
- **decorator** — Klassen mit EMFPy-Registry-Decorators (`@register_package` u. Ä.).

## Phasen

### Phase 0 — Scaffolding  🔄 (aktuell)
- `pyproject.toml` (Paket `emf_codegen`, py3.11+, deps `emf`+`jinja2`, dev-Extra), Tooling
  (pytest/ruff/mypy), CLI-Entry-Point, leeres Paketgerüst, Smoke-Test.
- **DoD:** `pip install -e ../EMFPy-core` (EMFPy) + `pip install -e .[dev]`, `pytest`/`ruff`/`mypy` laufen.

### Phase 1 — Loader + GenModel  ✅ ABGESCHLOSSEN
Spiegelt: `loader/EcoreLoader`, `genmodel/*`.
- `EcoreLoader.load(path)` → `EPackage` via EMFPy `XMIResource`; Mehrfach-/Dependency-Load.
- Internes Generierungsmodell: `GenModel`/`GenPackage`/`GenClass`/`GenFeature`/`GenEnum`/
  `GenDataType`/`GenOperation` + `GenerationMode`/`PropertyMode`.
- **Tests:** Loader lädt `library.ecore`; GenModel-Navigation.

### Phase 2 — GenConfig  ✅ ABGESCHLOSSEN
Spiegelt: `genconfig/GenConfig`, `GenConfigLoader`, `GenConfigConverter`.
- Konfig-Datentypen; Laden von `.genconfig.xmi`; Konvertierung GenConfig → GenModel
  (Modus, Output-Dir, Klassen-/Feature-Overrides, Defaults).
- **Tests (Port):** `genconfig-loader`.

### Phase 3 — Generator-Kern + plain-Modus  ✅ ABGESCHLOSSEN
Spiegelt: `generator/{TypeMapper, ImportResolver, GeneratorContext, GeneratedFile,
GeneratorOptions, CodeGenerator}`, `modes/{BaseGenerator, PlainGenerator}`, `templates/plain`.
- `TypeMapper` (Ecore→Python), `ImportResolver`, `CodeGenerator`-Orchestrierung, Jinja2-Setup.
- plain-Templates erzeugen Python-Klassen/Enums/Interfaces/Package.
- **Tests:** plain-Generierung der Library; generierter Code importierbar/lauffähig.

### Phase 4 — emf- + decorator-Modus  ✅ ABGESCHLOSSEN
Spiegelt: `modes/{EmfGenerator, DecoratorGenerator}`, `templates/{emf,decorator}`.
- **decorator:** Dataclasses mit `ECLASS_URI`-ClassVar + `field(metadata={kind,type,many})`
  (Python-Äquivalent der TS-`@ModelClass`/`@Attribute`/`@Reference`-Dekoratoren).
- **emf:** konkrete, typisierte `EObject`-Subklassen (eine pro `EClass`) mit `@property`-
  Accessoren, die an `e_get`/`e_set` delegieren (→ volle EMF-Semantik: Opposites, Containment,
  Container-Ref), plus `<prefix>_package`-Modul (EPackage + Klassen-/Feature-Literale),
  Factory und `__init__`-Barrel. Generierter Code ist lauffähig **und** `mypy --strict` clean.
- **Tests:** `test_decorator_generator` (4), `test_emf_generator` (7) — generierter Code
  wird importiert und gegen die EMFPy-Runtime ausgeführt.

### Phase 5 — Service-Interfaces + REST-Client  ⊘ ENTFÄLLT
Nischengeneratoren (DDSR-Broker / `rest-api.ecore`), für die Python-Variante bewusst
weggelassen. Kann später als eigenständige Erweiterung nachgezogen werden.

### Phase 6 — CLI  ✅ ABGESCHLOSSEN
Spiegelt: `cli/index` + `commands/{generate, init}` (REST-/Service-Befehle entfallen).
- argparse-Subcommands; `emfpy-codegen generate -m … -c … -o …`, `emfpy-codegen init …`.
- **Tests:** `test_cli` (3) — help, init, init→generate-Round-trip.

### Phase 7 — Beispiel & Round-trip  ✅ ABGESCHLOSSEN
- `examples/model/library.ecore` + `library.genconfig.xmi`; `generate:example`-Äquivalent;
  generiertes Artefakt unter `examples/generated/`, importiert + ausgeführt.
- **Tests:** `test_example_generation` (2) — End-to-End über die echte genconfig (mode=emf).

### Phase 8 — Politur & Konformität  ✅ ABGESCHLOSSEN
- README/Docs, Beispiele, Konformitäts-Review.
- **DoD:** alle Tests grün (46); Beispiel-Generierung läuft; ruff + mypy --strict clean.

## Test-Strategie
Die vitest-Suite von `emfts-codegen` ist das Konformitäts-Orakel. Da die Zielsprache abweicht
(Python statt TS), werden **Verhalten/Struktur** portiert (welche Dateien/Klassen/Features mit
welchen Eigenschaften entstehen), nicht der exakte TS-Text. Generierter Python-Code wird gegen
die EMFPy-Runtime ausgeführt.

## Risiken / offene Punkte
- `.genconfig.xmi`-Format (eigenes Ecore-Konfigmodell) sorgfältig gegen `genconfig.ecore`
  abgleichen.
- Template-Portierung EJS→Jinja2: Logik in Templates minimieren, in den Generator ziehen.
- Generierter Code muss idiomatisches Python sein (nicht 1:1 TS-Struktur).
