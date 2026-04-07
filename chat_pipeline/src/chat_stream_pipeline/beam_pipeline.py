"""Assemble the end-to-end Beam graph for streaming ingestion."""

from __future__ import annotations

import apache_beam as beam
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.io.gcp.pubsub import ReadFromPubSub, WriteToPubSub
from apache_beam.options.pipeline_options import PipelineOptions

from chat_stream_pipeline.config import PipelineSettings
from chat_stream_pipeline.schemas import conversations_table_schema, orders_table_schema
from chat_stream_pipeline.transforms import apply_fanout_step, apply_parse_step, flatten_error_streams


def run_streaming_pipeline(settings: PipelineSettings) -> None:
    """Build and run the streaming pipeline until externally cancelled."""

    options = PipelineOptions(settings.pipeline_options_argv())

    with beam.Pipeline(options=options) as pipeline:
        messages = pipeline | "Read Pub/Sub" >> ReadFromPubSub(subscription=settings.subscription)

        parsed, parse_errors = apply_parse_step(messages)
        conversations, orders, fanout_errors = apply_fanout_step(parsed)

        all_errors = flatten_error_streams(parse_errors, fanout_errors)

        if settings.errors_topic:
            _ = all_errors | "Write errors to Pub/Sub" >> WriteToPubSub(topic=settings.errors_topic)

        conversations_schema = conversations_table_schema()
        orders_schema = orders_table_schema()

        _ = conversations | "Write conversations to BigQuery" >> WriteToBigQuery(
            table=settings.bq_conversations_table,
            schema=conversations_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )

        _ = orders | "Write orders to BigQuery" >> WriteToBigQuery(
            table=settings.bq_orders_table,
            schema=orders_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )


def describe_graph(settings: PipelineSettings) -> str:
    """Human-readable summary for operators and integration tests."""

    lines = [
        "Streaming graph:",
        f"  subscription: {settings.subscription}",
        f"  conversations: {settings.bq_conversations_table}",
        f"  orders: {settings.bq_orders_table}",
        f"  runner: {settings.runner}",
        f"  errors_topic: {settings.errors_topic or '(metrics only)'}",
    ]
    return "\n".join(lines)
