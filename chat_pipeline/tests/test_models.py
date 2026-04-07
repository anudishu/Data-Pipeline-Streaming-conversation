"""Tests for shared domain models."""

from __future__ import annotations

import json

from chat_stream_pipeline.models import PipelineErrorPayload, decode_raw_preview


def test_pipeline_error_payload_roundtrip():
    payload = PipelineErrorPayload(kind="parse_error", detail="boom", raw_preview='{"a":1}')
    raw = payload.to_pubsub_bytes()
    assert json.loads(raw.decode("utf-8"))["kind"] == "parse_error"


def test_decode_raw_preview_truncates():
    big = b"x" * 9000
    text = decode_raw_preview(big, max_chars=100)
    assert text.endswith("…")
    assert len(text) == 101
