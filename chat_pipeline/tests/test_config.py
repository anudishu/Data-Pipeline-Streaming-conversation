"""Configuration parsing tests."""

from __future__ import annotations

from chat_stream_pipeline.config import parse_pipeline_settings, parse_publisher_settings


def test_parse_pipeline_settings_minimal():
    settings = parse_pipeline_settings(
        [
            "--subscription",
            "projects/p/subscriptions/s",
            "--bq_conversations_table",
            "p:d.c",
            "--bq_orders_table",
            "p:d.o",
        ]
    )
    assert settings.subscription == "projects/p/subscriptions/s"
    assert settings.errors_topic is None
    argv = settings.pipeline_options_argv()
    assert "--streaming" in argv
    assert any(a.startswith("--runner=") for a in argv)


def test_parse_publisher_settings():
    settings = parse_publisher_settings(
        [
            "--project",
            "demo",
            "--topic",
            "t1",
            "--bucket",
            "b1",
            "--object",
            "obj.jsonl",
            "--sleep_seconds",
            "0.5",
        ]
    )
    assert settings.object_name == "obj.jsonl"
    assert settings.sleep_seconds == 0.5
    assert settings.dry_run is False
