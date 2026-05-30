from __future__ import annotations

import argparse

from .cpu_collector import collect_and_update_history
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
        default="data/history.json",
        help="CPU JSON input path. Default: data/history.json",
    )
    generate.add_argument(
        "--sample",
        default="data/latest_cpu_sample.json",
        help="Latest sar sample JSON path. Default: data/latest_cpu_sample.json",
    )

    collect = subparsers.add_parser("collect-cpu", help="Run sar and update CPU history")
    collect.add_argument("--host", default="local", help="Host label. Default: local")
    collect.add_argument("--interval", type=int, default=2, help="sar interval seconds. Default: 2")
    collect.add_argument("--count", type=int, default=10, help="sar sample count. Default: 10")
    collect.add_argument(
        "--history",
        default="data/history.json",
        help="Daily max CPU history path. Default: data/history.json",
    )
    collect.add_argument(
        "--sample",
        default="data/latest_cpu_sample.json",
        help="Latest raw sample JSON path. Default: data/latest_cpu_sample.json",
    )
    collect.add_argument(
        "--sar-output-file",
        help="Read sar output from a file instead of running sar. Useful for local testing.",
    )
    collect.add_argument(
        "--date",
        help="Override collection date in YYYY-MM-DD format. Useful for tests.",
    )
    collect.add_argument(
        "--generate-page",
        action="store_true",
        help="Regenerate docs/index.html after updating history.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate-page":
        output_path = write_html(args.output, args.data, args.sample)
        print(f"Generated {output_path}")
        return

    if args.command == "collect-cpu":
        sar_output = None
        if args.sar_output_file:
            with open(args.sar_output_file, encoding="utf-8") as file:
                sar_output = file.read()

        collection = collect_and_update_history(
            history_path=args.history,
            sample_path=args.sample,
            host=args.host,
            interval=args.interval,
            count=args.count,
            sar_output=sar_output,
            collected_date=args.date,
        )
        print(
            f"Collected {len(collection.samples)} samples for {collection.host}; "
            f"daily max CPU is {collection.max_cpu:.1f}%"
        )
        if args.generate_page:
            output_path = write_html("docs/index.html", args.history, args.sample)
            print(f"Generated {output_path}")
        return

    print(greeting())
