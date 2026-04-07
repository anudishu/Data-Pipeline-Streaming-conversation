"""Sample data generator tests."""

from __future__ import annotations

import json
import tempfile

from chat_stream_pipeline.data_generator import GeneratorConfig, generate_dataset, write_jsonl


def test_generate_dataset_shape():
    config = GeneratorConfig(
        conversation_groups=2,
        min_messages=2,
        max_messages=5,
        seed=123,
        start_time=__import__("datetime").datetime(2024, 1, 1, tzinfo=__import__("datetime").timezone.utc),
        output_path="unused",
    )
    lines = list(generate_dataset(config))
    assert len(lines) >= 2
    city_rows = [row for row in lines if set(row.keys()) == {"orderId", "cityCode"}]
    assert len(city_rows) == 2


def test_write_jsonl_roundtrip():
    config = GeneratorConfig(
        conversation_groups=1,
        min_messages=2,
        max_messages=3,
        seed=7,
        start_time=__import__("datetime").datetime(2024, 1, 1, tzinfo=__import__("datetime").timezone.utc),
        output_path="unused",
    )
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
    path.close()
    try:
        total = write_jsonl(path.name, generate_dataset(config))
        assert total > 0
        with open(path.name, encoding="utf-8") as handle:
            first = json.loads(handle.readline())
        assert "orderId" in first
    finally:
        __import__("os").unlink(path.name)
