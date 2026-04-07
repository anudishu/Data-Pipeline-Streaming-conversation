"""Apache Beam transforms: parse Pub/Sub payloads, count failures, fan out to sinks."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator

import apache_beam as beam
from apache_beam import pvalue
from apache_beam.metrics import Metrics

from chat_stream_pipeline.constants import (
    ERROR_KIND_NOT_OBJECT,
    ERROR_KIND_PARSE,
    ERROR_KIND_UNROUTABLE,
    METRICS_NAMESPACE,
)
from chat_stream_pipeline.models import PipelineErrorPayload, decode_raw_preview
from chat_stream_pipeline.row_builders import route_parsed_object


class ParsePubSubJson(beam.DoFn):
    """
    Decode UTF-8, parse JSON, and route parse failures to a side output.

    Main output: ``dict`` payloads only.
    Side output ``FAILURES``: ``bytes`` suitable for ``WriteToPubSub``.
    """

    TAG_FAILURES = "failures"

    def __init__(self) -> None:
        super().__init__()
        self._parse_errors = Metrics.counter(METRICS_NAMESPACE, "json_parse_errors")
        self._not_object = Metrics.counter(METRICS_NAMESPACE, "json_not_object")

    def process(self, element: bytes) -> Iterator[Any]:
        try:
            text = element.decode("utf-8")
            obj = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._parse_errors.inc()
            payload = PipelineErrorPayload(
                kind=ERROR_KIND_PARSE,
                detail=str(exc),
                raw_preview=decode_raw_preview(element),
            )
            yield pvalue.TaggedOutput(self.TAG_FAILURES, payload.to_pubsub_bytes())
            return

        if not isinstance(obj, dict):
            self._not_object.inc()
            payload = PipelineErrorPayload(
                kind=ERROR_KIND_NOT_OBJECT,
                detail="top_level_not_object",
                raw_preview=decode_raw_preview(element),
            )
            yield pvalue.TaggedOutput(self.TAG_FAILURES, payload.to_pubsub_bytes())
            return

        yield obj


class FanOutRows(beam.DoFn):
    """
    From each parsed object emit zero or one conversation row, zero or one order row,
    and optionally an unroutable error record.
    """

    TAG_FAILURES = "failures"

    def __init__(self) -> None:
        super().__init__()
        self._unroutable = Metrics.counter(METRICS_NAMESPACE, "unroutable_records")
        self._conversation_out = Metrics.counter(METRICS_NAMESPACE, "conversation_rows_emitted")
        self._order_out = Metrics.counter(METRICS_NAMESPACE, "order_rows_emitted")

    def process(self, element: Dict[str, Any]) -> Iterator[Any]:
        conv, order, unroutable = route_parsed_object(element)
        if conv is not None:
            self._conversation_out.inc()
            yield pvalue.TaggedOutput("conversations", conv)
        if order is not None:
            self._order_out.inc()
            yield pvalue.TaggedOutput("orders", order)
        if unroutable:
            self._unroutable.inc()
            raw_preview = json.dumps(element, separators=(",", ":"), ensure_ascii=False)
            if len(raw_preview) > 8192:
                raw_preview = raw_preview[:8192] + "…"
            payload = PipelineErrorPayload(
                kind=ERROR_KIND_UNROUTABLE,
                detail="no_conversation_or_order_branch",
                raw_preview=raw_preview,
            )
            yield pvalue.TaggedOutput(self.TAG_FAILURES, payload.to_pubsub_bytes())


def flatten_error_streams(
    parse_failures: beam.PCollection,
    fanout_failures: beam.PCollection,
) -> beam.PCollection:
    """Merge side outputs that share the same Pub/Sub wire format (UTF-8 JSON bytes)."""

    return (parse_failures, fanout_failures) | "FlattenErrors" >> beam.Flatten()


def apply_parse_step(
    raw_messages: beam.PCollection,
) -> tuple[beam.PCollection, beam.PCollection]:
    """
    Returns:
        (parsed_dicts, error_bytes_for_pubsub)
    """

    parsed = raw_messages | "Parse JSON" >> beam.ParDo(ParsePubSubJson()).with_outputs(
        ParsePubSubJson.TAG_FAILURES,
        main="parsed",
    )
    return parsed["parsed"], parsed[ParsePubSubJson.TAG_FAILURES]


def apply_fanout_step(
    parsed: beam.PCollection,
) -> tuple[beam.PCollection, beam.PCollection, beam.PCollection]:
    """
    Returns:
        (conversations, orders, error_bytes_for_pubsub)
    """

    routed = parsed | "Fan out rows" >> beam.ParDo(FanOutRows()).with_outputs(
        "conversations",
        "orders",
        FanOutRows.TAG_FAILURES,
    )
    failures_tag = FanOutRows.TAG_FAILURES
    return routed["conversations"], routed["orders"], routed[failures_tag]
