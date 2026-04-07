"""BigQuery table schemas shared by Beam ``WriteToBigQuery`` and documentation."""

from __future__ import annotations

from typing import Any


def conversations_table_schema() -> dict[str, Any]:
    return {
        "fields": [
            {"name": "senderAppType", "type": "STRING"},
            {"name": "courierId", "type": "INTEGER"},
            {"name": "fromId", "type": "INTEGER"},
            {"name": "toId", "type": "INTEGER"},
            {"name": "chatStartedByMessage", "type": "BOOLEAN"},
            {"name": "orderId", "type": "INTEGER"},
            {"name": "orderStage", "type": "STRING"},
            {"name": "customerId", "type": "INTEGER"},
            {"name": "messageSentTime", "type": "TIMESTAMP"},
        ]
    }


def orders_table_schema() -> dict[str, Any]:
    return {
        "fields": [
            {"name": "cityCode", "type": "STRING"},
            {"name": "orderId", "type": "INTEGER"},
        ]
    }


def schema_field_names(schema: dict[str, Any]) -> list[str]:
    fields = schema.get("fields") or []
    return [str(f["name"]) for f in fields if isinstance(f, dict) and "name" in f]
