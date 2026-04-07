"""Apache Beam transform tests (DirectRunner / TestPipeline)."""

from __future__ import annotations

import json

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from apache_beam.transforms import combiners

from chat_stream_pipeline.row_builders import build_conversation_row, build_order_row
from chat_stream_pipeline.transforms import FanOutRows, ParsePubSubJson


def test_parse_pubsub_json_success_and_failure():
    good = json.dumps({"orderId": 1, "cityCode": "NYC"}).encode("utf-8")
    bad = b"{not-json"

    with TestPipeline() as p:
        result = p | beam.Create([good, bad]) | beam.ParDo(ParsePubSubJson()).with_outputs(
            ParsePubSubJson.TAG_FAILURES,
            main="parsed",
        )
        assert_that(
            result.parsed,
            equal_to([{"orderId": 1, "cityCode": "NYC"}]),
            label="assert_parse_ok",
        )
        failure_count = result[ParsePubSubJson.TAG_FAILURES] | "CountFailures" >> combiners.Count.Globally()
        assert_that(failure_count, equal_to([1]), label="assert_parse_failures")


def test_fan_out_rows_splits_branches():
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
    expected_conv = build_conversation_row(payload)
    expected_order = build_order_row(payload)

    with TestPipeline() as p:
        routed = p | beam.Create([payload]) | beam.ParDo(FanOutRows()).with_outputs(
            "conversations",
            "orders",
            FanOutRows.TAG_FAILURES,
        )
        assert_that(routed.conversations, equal_to([expected_conv]), label="assert_fanout_conversations")
        assert_that(routed.orders, equal_to([expected_order]), label="assert_fanout_orders")
        failure_count = routed[FanOutRows.TAG_FAILURES] | combiners.Count.Globally()
        assert_that(failure_count, equal_to([0]), label="assert_fanout_failures")
