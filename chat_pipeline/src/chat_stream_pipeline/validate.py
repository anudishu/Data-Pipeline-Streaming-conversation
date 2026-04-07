"""JSONL shape validation for the bundled sample export and CI gates."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from chat_stream_pipeline.models import RecordKind, classify_record as classify_record_kind


@dataclass
class Summary:
    lines: int = 0
    blanks: int = 0
    json_errors: int = 0
    conversation_rows: int = 0
    order_city_rows: int = 0
    unknown_rows: int = 0


def classify_record(obj: dict[str, Any]) -> str:
    """Return legacy string labels expected by existing shell scripts and tests."""

    kind = classify_record_kind(obj)
    if kind is RecordKind.ORDER_CITY:
        return "order_city"
    if kind is RecordKind.CONVERSATION:
        return "conversation"
    return "unknown"


def iter_jsonl_lines(path: str) -> Iterable[str]:
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            yield raw.rstrip("\n")


def validate_file(path: str, fail_on_unknown: bool, max_unknown: int) -> Summary:
    summary = Summary()
    for line in iter_jsonl_lines(path):
        summary.lines += 1
        if line.strip() == "":
            summary.blanks += 1
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            summary.json_errors += 1
            continue
        if not isinstance(obj, dict):
            summary.unknown_rows += 1
            continue

        kind = classify_record(obj)
        if kind == "order_city":
            summary.order_city_rows += 1
        elif kind == "conversation":
            summary.conversation_rows += 1
        else:
            summary.unknown_rows += 1

    if summary.json_errors > 0:
        return summary

    if summary.conversation_rows == 0 and summary.order_city_rows == 0:
        return summary

    if fail_on_unknown and summary.unknown_rows > 0:
        return summary

    if summary.unknown_rows > max_unknown:
        return summary

    return summary


def build_validate_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate newline-delimited JSON chat export shapes.")
    parser.add_argument("--path", required=True, help="Path to JSONL file.")
    parser.add_argument(
        "--fail-on-unknown",
        action="store_true",
        help="Exit non-zero if any row does not match known shapes.",
    )
    parser.add_argument(
        "--max-unknown",
        type=int,
        default=0,
        help="Allow up to N unknown rows before failing (with --fail-on-unknown).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_validate_arg_parser()
    args = parser.parse_args(argv)

    summary = validate_file(args.path, args.fail_on_unknown, args.max_unknown)

    print(
        json.dumps(
            {
                "lines": summary.lines,
                "blanks": summary.blanks,
                "json_errors": summary.json_errors,
                "conversation_rows": summary.conversation_rows,
                "order_city_rows": summary.order_city_rows,
                "unknown_rows": summary.unknown_rows,
            },
            sort_keys=True,
        )
    )

    if summary.json_errors > 0:
        return 2

    if args.fail_on_unknown and summary.unknown_rows > args.max_unknown:
        return 3

    if summary.lines == 0:
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
