"""Operational smoke checks: Pub/Sub subscription presence and BigQuery freshness."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from google.api_core import exceptions as gcloud_exceptions
from google.cloud import bigquery, pubsub_v1

from chat_stream_pipeline.config import parse_health_settings
from chat_stream_pipeline.logging_utils import setup_logging


def check_subscription_exists(project: str, subscription_id: str) -> dict[str, Any]:
    subscriber = pubsub_v1.SubscriberClient()
    path = subscriber.subscription_path(project, subscription_id)
    try:
        sub = subscriber.get_subscription(request={"subscription": path})
        return {
            "ok": True,
            "subscription": sub.name,
            "topic": sub.topic,
        }
    except gcloud_exceptions.NotFound:
        return {"ok": False, "subscription": path, "error": "not_found"}


def count_recent_rows(
    client: bigquery.Client,
    project: str,
    dataset_id: str,
    table_id: str,
    timestamp_column: str,
    window: timedelta,
) -> int:
    table_ref = f"`{project}.{dataset_id}.{table_id}`"
    cutoff = datetime.now(timezone.utc) - window
    query = (
        f"SELECT COUNT(1) AS c FROM {table_ref} "
        f"WHERE {timestamp_column} >= TIMESTAMP(@cutoff)"
    )
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("cutoff", "TIMESTAMP", cutoff),
        ]
    )
    rows = list(client.query(query, job_config=job_config).result())
    if not rows:
        return 0
    return int(rows[0]["c"])


def count_all_rows(
    client: bigquery.Client,
    project: str,
    dataset_id: str,
    table_id: str,
) -> int:
    table_ref = f"`{project}.{dataset_id}.{table_id}`"
    query = f"SELECT COUNT(1) AS c FROM {table_ref}"
    rows = list(client.query(query).result())
    if not rows:
        return 0
    return int(rows[0]["c"])


def fetch_sample_rows(
    client: bigquery.Client,
    project: str,
    dataset_id: str,
    table_id: str,
    order_clause: str,
    limit: int,
) -> list[dict[str, Any]]:
    table_ref = f"`{project}.{dataset_id}.{table_id}`"
    query = f"SELECT * FROM {table_ref} ORDER BY {order_clause} DESC LIMIT @lim"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("lim", "INT64", limit)],
    )
    return [dict(row) for row in client.query(query, job_config=job_config).result()]


def run_health_checks(settings: Any) -> dict[str, Any]:
    report: dict[str, Any] = {
        "project": settings.project,
        "subscription": settings.subscription,
        "dataset": settings.dataset_id,
    }

    report["pubsub"] = check_subscription_exists(settings.project, settings.subscription)

    client = bigquery.Client(project=settings.project)
    window = timedelta(hours=24)

    conv_recent = count_recent_rows(
        client,
        settings.project,
        settings.dataset_id,
        settings.conversations_table,
        "messageSentTime",
        window,
    )
    orders_total = count_all_rows(
        client,
        settings.project,
        settings.dataset_id,
        settings.orders_table,
    )

    report["bigquery"] = {
        "conversations_last_24h": conv_recent,
        "orders_total": orders_total,
        "conversations_sample": fetch_sample_rows(
            client,
            settings.project,
            settings.dataset_id,
            settings.conversations_table,
            "messageSentTime",
            settings.sample_limit,
        ),
        "orders_sample": fetch_sample_rows(
            client,
            settings.project,
            settings.dataset_id,
            settings.orders_table,
            "orderId",
            settings.sample_limit,
        ),
    }

    report["ok"] = bool(report["pubsub"].get("ok"))
    return report


def main(argv: Optional[list[str]] = None) -> int:
    setup_logging()
    log = logging.getLogger("chat_stream_pipeline.health")
    settings = parse_health_settings(argv)
    try:
        report = run_health_checks(settings)
    except Exception:
        log.exception("Health check failed")
        return 1

    print(json.dumps(report, default=str, indent=2, sort_keys=True))

    if not report.get("ok"):
        return 2

    bq = report.get("bigquery") or {}
    if int(bq.get("conversations_last_24h") or 0) == 0:
        log.warning("No conversation rows in the last 24h (pipeline may be idle or misconfigured).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
