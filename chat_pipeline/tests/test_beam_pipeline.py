"""Smoke tests for pipeline wiring without launching Dataflow."""

from __future__ import annotations

from chat_stream_pipeline.beam_pipeline import describe_graph
from chat_stream_pipeline.config import PipelineSettings


def test_describe_graph_includes_tables():
    settings = PipelineSettings(
        subscription="projects/p/subscriptions/s",
        bq_conversations_table="p:d.c",
        bq_orders_table="p:d.o",
        runner="DirectRunner",
        project="p",
        region="us-central1",
        temp_location=None,
        staging_location=None,
        job_name=None,
        service_account_email=None,
        errors_topic="projects/p/topics/errors",
    )
    text = describe_graph(settings)
    assert "projects/p/subscriptions/s" in text
    assert "p:d.c" in text
    assert "errors" in text
