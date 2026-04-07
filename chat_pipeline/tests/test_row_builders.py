"""Unit tests for row coercion and routing helpers."""

from __future__ import annotations

import pytest

from chat_stream_pipeline.row_builders import (
    build_conversation_row,
    build_order_row,
    coerce_int,
    route_parsed_object,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (True, None),
        (42, 42),
        ("99", 99),
        ("  -3 ", -3),
        ("", None),
        ("abc", None),
        (3.14, None),
    ],
)
def test_coerce_int(value, expected):
    assert coerce_int(value) == expected


def test_build_conversation_row_minimal():
    row = build_conversation_row(
        {
            "senderAppType": "Courier Android",
            "courierId": 1,
            "fromId": 1,
            "toId": 2,
            "chatStartedByMessage": True,
            "orderId": 9,
            "orderStage": "ACCEPTED",
            "customerId": 2,
            "messageSentTime": "2024-02-01T10:00:00Z",
        }
    )
    assert row is not None
    assert row["orderId"] == 9
    assert row["customerId"] == 2
    assert row["chatStartedByMessage"] is True


def test_build_conversation_row_rejects_missing_ids():
    assert build_conversation_row({"orderId": 1}) is None


def test_build_order_row_requires_city():
    assert build_order_row({"orderId": 1}) is None
    row = build_order_row({"orderId": 1, "cityCode": "NYC"})
    assert row == {"cityCode": "NYC", "orderId": 1}


def test_route_parsed_object_emits_both_branches():
    payload = {
        "senderAppType": "Courier Android",
        "courierId": 1,
        "fromId": 1,
        "toId": 2,
        "chatStartedByMessage": True,
        "orderId": 9,
        "orderStage": "ACCEPTED",
        "customerId": 2,
        "messageSentTime": "2024-02-01T10:00:00Z",
        "cityCode": "NYC",
    }
    conv, order, unroutable = route_parsed_object(payload)
    assert conv is not None
    assert order is not None
    assert unroutable is False


def test_route_parsed_object_unroutable():
    conv, order, unroutable = route_parsed_object({"note": "nothing"})
    assert conv is None
    assert order is None
    assert unroutable is True
