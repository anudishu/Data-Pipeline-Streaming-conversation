"""Generate synthetic JSONL chat + order enrichment data for demos and load tests."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator, Optional

from chat_stream_pipeline.constants import CITY_CODES, ORDER_STAGES, SENDER_APP_TYPES
from chat_stream_pipeline.logging_utils import setup_logging


@dataclass(frozen=True)
class GeneratorConfig:
    conversation_groups: int
    min_messages: int
    max_messages: int
    seed: Optional[int]
    start_time: datetime
    output_path: str


def _random_id(rng: random.Random, low: int = 10_000_000, high: int = 99_999_999) -> int:
    return rng.randint(low, high)


def generate_conversation_thread(rng: random.Random, cursor: datetime) -> tuple[list[dict[str, Any]], datetime]:
    """Produce chat messages plus a trailing city enrichment row sharing the same order id."""

    courier_id = _random_id(rng)
    customer_id = _random_id(rng)
    order_id = _random_id(rng)
    sender_type = rng.choice(SENDER_APP_TYPES)
    num_messages = rng.randint(2, 5)
    messages: list[dict[str, Any]] = []
    chat_started = True

    for _ in range(num_messages):
        if sender_type.startswith("Courier"):
            record = {
                "senderAppType": sender_type,
                "courierId": courier_id,
                "fromId": courier_id,
                "toId": customer_id,
                "chatStartedByMessage": chat_started,
                "orderId": order_id,
                "orderStage": rng.choice(ORDER_STAGES),
                "customerId": customer_id,
                "messageSentTime": cursor.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        else:
            record = {
                "senderAppType": sender_type,
                "customerId": customer_id,
                "fromId": customer_id,
                "toId": courier_id,
                "chatStartedByMessage": chat_started,
                "orderId": order_id,
                "orderStage": rng.choice(ORDER_STAGES),
                "courierId": courier_id,
                "messageSentTime": cursor.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        messages.append(record)
        chat_started = False
        sender_type = "Customer iOS" if sender_type.startswith("Courier") else "Courier Android"
        cursor = cursor + timedelta(seconds=rng.randint(1, 60))

    city_row = {"orderId": order_id, "cityCode": rng.choice(CITY_CODES)}
    messages.append(city_row)
    return messages, cursor


def generate_dataset(config: GeneratorConfig) -> Iterator[dict[str, Any]]:
    rng = random.Random(config.seed)
    cursor = config.start_time
    for _ in range(config.conversation_groups):
        thread, cursor = generate_conversation_thread(rng, cursor)
        yield from thread


def write_jsonl(path: str, records: Iterator[dict[str, Any]]) -> int:
    count = 0
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record, handle, separators=(",", ":"), ensure_ascii=False)
            handle.write("\n")
            count += 1
    return count


def build_generator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic JSONL for the streaming demo.")
    parser.add_argument("--output", default="conversations_generated.jsonl", help="Output JSONL path")
    parser.add_argument("--conversations", type=int, default=400, help="Number of synthetic conversation groups")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    parser.add_argument(
        "--start",
        default="2024-02-01T10:00:00Z",
        help="ISO8601 UTC start timestamp for the first message",
    )
    return parser


def parse_start_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def main(argv: Optional[list[str]] = None) -> int:
    import logging

    setup_logging()
    log = logging.getLogger("chat_stream_pipeline.data_generator")
    parser = build_generator_parser()
    args = parser.parse_args(argv)

    config = GeneratorConfig(
        conversation_groups=args.conversations,
        min_messages=2,
        max_messages=5,
        seed=args.seed,
        start_time=parse_start_time(args.start),
        output_path=args.output,
    )

    total = write_jsonl(config.output_path, generate_dataset(config))
    log.info("Wrote %s JSON lines to %s", total, config.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
