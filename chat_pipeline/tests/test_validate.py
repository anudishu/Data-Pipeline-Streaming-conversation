"""Tests for JSONL validation utilities."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from chat_stream_pipeline.validate import classify_record, validate_file


def test_classify_order_city():
    assert classify_record({"orderId": 12, "cityCode": "NYC"}) == "order_city"


def test_classify_conversation():
    obj = {
        "senderAppType": "Courier Android",
        "fromId": 1,
        "toId": 2,
        "chatStartedByMessage": True,
        "orderId": 9,
        "orderStage": "ACCEPTED",
        "customerId": 2,
        "messageSentTime": "2024-02-01T10:00:00Z",
        "courierId": 1,
    }
    assert classify_record(obj) == "conversation"


def test_classify_unknown():
    assert classify_record({"orderId": 9}) == "unknown"


def test_validate_file_happy_path():
    lines = [
        json.dumps(
            {
                "senderAppType": "Courier Android",
                "fromId": 1,
                "toId": 2,
                "chatStartedByMessage": True,
                "orderId": 9,
                "orderStage": "ACCEPTED",
                "customerId": 2,
                "messageSentTime": "2024-02-01T10:00:00Z",
                "courierId": 1,
            },
            separators=(",", ":"),
        ),
        json.dumps({"orderId": 9, "cityCode": "NYC"}, separators=(",", ":")),
    ]
    path = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    try:
        for line in lines:
            path.write(line + "\n")
        path.close()
        summary = validate_file(path.name, fail_on_unknown=True, max_unknown=0)
        assert summary.json_errors == 0
        assert summary.conversation_rows == 1
        assert summary.order_city_rows == 1
        assert summary.unknown_rows == 0
    finally:
        os.unlink(path.name)


def test_validate_file_json_error():
    path = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    try:
        path.write("not-json\n")
        path.close()
        summary = validate_file(path.name, fail_on_unknown=False, max_unknown=0)
        assert summary.json_errors == 1
    finally:
        os.unlink(path.name)
