"""Typed structures and helpers describing inbound chat and order events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class RecordKind(str, Enum):
    """High-level classification for a JSONL record in the sample export."""

    CONVERSATION = "conversation"
    ORDER_CITY = "order_city"
    UNKNOWN = "unknown"


JsonObject = Mapping[str, Any]


def is_int_value(value: Any) -> bool:
    """True for integers that are not bools (JSON treats bool as int in Python)."""

    return isinstance(value, int) and not isinstance(value, bool)


def is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def has_order_city_shape(obj: JsonObject) -> bool:
    """Minimal two-field order enrichment row: orderId + cityCode."""

    if "orderId" not in obj or "cityCode" not in obj:
        return False
    if len(obj.keys()) > 3:
        return False
    if not is_int_value(obj.get("orderId")):
        return False
    if not is_non_empty_str(obj.get("cityCode")):
        return False
    return True


def has_conversation_shape(obj: JsonObject) -> bool:
    """Conversation message row with the fields used by BigQuery conversations table."""

    required = (
        "senderAppType",
        "fromId",
        "toId",
        "chatStartedByMessage",
        "orderId",
        "orderStage",
        "customerId",
        "messageSentTime",
    )
    if not all(k in obj for k in required):
        return False
    if not is_non_empty_str(obj.get("senderAppType")):
        return False
    if not isinstance(obj.get("chatStartedByMessage"), bool):
        return False
    if not is_non_empty_str(obj.get("orderStage")):
        return False
    if not is_non_empty_str(obj.get("messageSentTime")):
        return False
    ids = (obj.get("fromId"), obj.get("toId"), obj.get("orderId"), obj.get("customerId"))
    if not all(is_int_value(v) for v in ids):
        return False
    courier = obj.get("courierId")
    if courier is not None and not is_int_value(courier):
        return False
    return True


def classify_record(obj: JsonObject) -> RecordKind:
    if has_order_city_shape(obj):
        return RecordKind.ORDER_CITY
    if has_conversation_shape(obj):
        return RecordKind.CONVERSATION
    return RecordKind.UNKNOWN


@dataclass(frozen=True)
class ConversationRow:
    """Normalized row matching the BigQuery ``conversations`` table."""

    senderAppType: str
    courierId: Optional[int]
    fromId: Optional[int]
    toId: Optional[int]
    chatStartedByMessage: bool
    orderId: int
    orderStage: str
    customerId: int
    messageSentTime: Any

    def as_bigquery_dict(self) -> dict[str, Any]:
        return {
            "senderAppType": self.senderAppType,
            "courierId": self.courierId,
            "fromId": self.fromId,
            "toId": self.toId,
            "chatStartedByMessage": self.chatStartedByMessage,
            "orderId": self.orderId,
            "orderStage": self.orderStage,
            "customerId": self.customerId,
            "messageSentTime": self.messageSentTime,
        }


@dataclass(frozen=True)
class OrderRow:
    """Normalized row matching the BigQuery ``orders`` table."""

    cityCode: str
    orderId: int

    def as_bigquery_dict(self) -> dict[str, Any]:
        return {"cityCode": self.cityCode, "orderId": self.orderId}


@dataclass(frozen=True)
class PipelineErrorPayload:
    """Serializable descriptor for records sent to the optional errors topic."""

    kind: str
    detail: str
    raw_preview: str

    def to_pubsub_bytes(self) -> bytes:
        import json

        body: dict[str, Any] = {
            "kind": self.kind,
            "detail": self.detail,
            "raw_preview": self.raw_preview,
        }
        return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_raw_preview(raw: bytes, max_chars: int = 8192) -> str:
    """Best-effort UTF-8 decode with truncation for logging and error topics."""

    text = raw.decode("utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "…"
    return text


def summarize_payload_for_error(raw: bytes) -> str:
    return decode_raw_preview(raw, max_chars=2048)
