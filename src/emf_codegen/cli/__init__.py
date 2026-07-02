"""Command-line interface for emf-codegen (``emfpy-codegen``).

Mirrors the commander-based CLI of ``emfts-codegen`` using stdlib ``argparse``.
Implemented subcommands: ``generate`` and ``init``. (The service-interface and
REST-client commands of the TS tool are intentionally out of scope.)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from emf_codegen import generate as run_generate
from emf_codegen.loader import EcoreLoader
from emf_codegen.util.string_utils import capitalize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emfpy-codegen",
        description="Python code generator for Ecore models using EMFPy",
    )
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Generate Python code from an Ecore model")
    gen.add_argument("-m", "--model", required=True, help="Path to .ecore model file")
    gen.add_argument("-c", "--config", required=True, help="Path to .genconfig.xmi file")
    gen.add_argument("-o", "--output", help="Output directory override")
    gen.add_argument(
        "-d", "--dependency", action="append", default=[],
        help="Dependent .ecore model (loaded first); repeatable",
    )
    gen.add_argument(
        "--import-mapping", action="append", default=[],
        help="Referenced-package mapping nsURI=importPath; repeatable",
    )
    gen.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    gen.set_defaults(func=_cmd_generate)

    init = sub.add_parser("init", help="Initialize a GenConfig from an Ecore model")
    init.add_argument("-m", "--model", required=True, help="Path to .ecore model file")
    init.add_argument("-o", "--output", help="Output path for the .genconfig.xmi file")
    init.add_argument(
        "--mode", default="emf", choices=["plain", "decorator", "emf"],
        help="Generation mode (default: emf)",
    )
    init.add_argument("--base-package", default="", help="Base package path for generated code")
    init.add_argument("--prefix", help="Prefix for generated class names")
    init.add_argument("--output-dir", default="./generated", help="Output dir for generated code")
    init.set_defaults(func=_cmd_init)

    return parser


def _cmd_generate(args: argparse.Namespace) -> int:
    referenced: dict[str, str] = {}
    for mapping in args.import_mapping:
        key, sep, value = mapping.partition("=")
        if not sep:
            print(f"[WARN] Invalid import mapping (expected nsURI=importPath): {mapping}")
            continue
        referenced[key] = value

    if args.verbose:
        print(f"Loading Ecore model: {args.model}")
        for dep in args.dependency:
            print(f"Loading dependency: {dep}")

    print("Generating code...")
    result = run_generate(
        args.model,
        args.config,
        output_dir=args.output,
        dependencies=args.dependency,
        referenced_packages=referenced or None,
    )

    for diag in result.diagnostics:
        if diag.level == "error":
            print(f"[ERROR] {diag.message}")
        elif diag.level == "warning":
            print(f"[WARN] {diag.message}")
        elif args.verbose:
            print(f"[INFO] {diag.message}")

    if not result.success:
        print("Generation failed with errors")
        return 1

    written = [f for f in result.files if f.generated]
    out_dir = args.output or "(genconfig outputDir)"
    print(f"Successfully generated {len(written)} files to {out_dir}")
    if args.verbose:
        for file in written:
            print(f"  - {file.path}")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    print(f"Loading Ecore model: {args.model}")
    e_package = EcoreLoader().load(args.model)
    package_name = e_package.name or "Model"
    ns_uri = e_package.ns_uri or f"http://example.org/{package_name.lower()}"
    print(f"Loaded package: {package_name} nsURI: {ns_uri}")

    prefix = args.prefix or capitalize(package_name)
    content = _genconfig_xmi(ns_uri, args.mode, args.output_dir, prefix, args.base_package)

    output_path = args.output or _default_config_path(args.model)
    Path(output_path).write_text(content, encoding="utf-8")

    print(f"Created GenConfig: {output_path}")
    print(f"Mode: {args.mode}")
    print(f"Prefix: {prefix}")
    print(f"Base package: {args.base_package or '(none)'}")
    print(f"Output directory: {args.output_dir}")
    return 0


def _default_config_path(model_path: str) -> str:
    path = Path(model_path)
    if path.suffix == ".ecore":
        return str(path.with_suffix(".genconfig.xmi"))
    return f"{model_path}.genconfig.xmi"


def _genconfig_xmi(
    ns_uri: str, mode: str, output_dir: str, prefix: str, base_package: str
) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<genconfig:GenConfig
    xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:genconfig="http://www.emfts.org/genconfig/1.0"
    ecorePackage="{ns_uri}#/">
  <generation mode="{mode}" outputDir="{output_dir}" fileExtension=".py"/>
  <package prefix="{prefix}" basePackage="{base_package}"
      generateFactory="true" generatePackage="true" generateIndex="true"/>
  <classDefaults generateInterface="true" generateImpl="true" rootExtendsClass="EObject"/>
  <featureDefaults notify="true" property="editable"/>
</genconfig:GenConfig>
"""


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    try:
        result: int = func(args)
        return result
    except Exception as exc:  # noqa: BLE001 - top-level CLI guard
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
