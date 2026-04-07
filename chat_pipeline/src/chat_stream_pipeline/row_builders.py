"""Pure functions turning raw JSON objects into BigQuery-ready dictionaries."""

from __future__ import annotations

from typing import Any, Dict, Optional

from chat_stream_pipeline.constants import NA
from chat_stream_pipeline.models import ConversationRow, JsonObject, OrderRow, classify_record, RecordKind


def coerce_int(value: Any) -> Optional[int]:
    """
    Coerce JSON/Python values to int for identifiers.

    Accepts integers and (optionally) base-10 string forms seen in loose producers.
    Rejects bool because JSON ``true``/``false`` must not become ``1``/``0``.
    """

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.lstrip("-").isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
            try:
                return int(stripped, 10)
            except ValueError:
                return None
    return None


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return False


def as_text(value: Any, default: str = NA) -> str:
    if value is None:
        return default
    if isinstance(value, str) and value.strip() != "":
        return value
    return default


def build_conversation_row(data: JsonObject) -> Optional[Dict[str, Any]]:
    """
    Map a JSON object to a conversations table row dict.

    Returns ``None`` when required identifiers are missing so the record can be skipped
    or treated as unroutable upstream.
    """

    order_id = coerce_int(data.get("orderId"))
    customer_id = coerce_int(data.get("customerId"))
    if order_id is None or customer_id is None:
        return None

    row = ConversationRow(
        senderAppType=as_text(data.get("senderAppType"), NA),
        courierId=coerce_int(data.get("courierId")),
        fromId=coerce_int(data.get("fromId")),
        toId=coerce_int(data.get("toId")),
        chatStartedByMessage=coerce_bool(data.get("chatStartedByMessage")),
        orderId=order_id,
        orderStage=as_text(data.get("orderStage"), NA),
        customerId=customer_id,
        messageSentTime=data.get("messageSentTime"),
    )
    return row.as_bigquery_dict()


def build_order_row(data: JsonObject) -> Optional[Dict[str, Any]]:
    """Map a JSON object to an orders table row dict."""

    order_id = coerce_int(data.get("orderId"))
    city = as_text(data.get("cityCode"), NA)
    if order_id is None:
        return None
    if city == NA:
        return None
    return OrderRow(cityCode=city, orderId=order_id).as_bigquery_dict()


def route_parsed_object(
    data: JsonObject,
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], bool]:
    """
    Given a parsed JSON object, produce conversation and order row candidates.

    Returns:
        (conversation_dict_or_none, order_dict_or_none, is_unroutable)

    ``is_unroutable`` is True when the object is a dict but neither branch produced a row.
    """

    conv = build_conversation_row(data)
    order = build_order_row(data)
    unroutable = conv is None and order is None
    return conv, order, unroutable


def record_kind_for_object(obj: JsonObject) -> str:
    """String kind for validation CLI compatibility (conversation | order_city | unknown)."""

    kind = classify_record(obj)
    if kind is RecordKind.ORDER_CITY:
        return "order_city"
    if kind is RecordKind.CONVERSATION:
        return "conversation"
    return "unknown"
