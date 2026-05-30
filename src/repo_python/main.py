from __future__ import annotations

import argparse

from .page_generator import write_html


def greeting(name: str = "Python project") -> str:
    return f"Hello from {name}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="repo_python command-line tools")
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate-page", help="Generate an HTML web page")
    generate.add_argument(
        "--output",
        default="docs/index.html",
        help="HTML output path. Default: docs/index.html",
    )
    generate.add_argument(
        "--data",
        default="data/cpu_usage.json",
        help="CPU JSON input path. Default: data/cpu_usage.json",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate-page":
        output_path = write_html(args.output, args.data)
        print(f"Generated {output_path}")
        return

    print(greeting())
