"""Shared constants for the chat streaming domain."""

NA = "N/A"

# Beam I/O and metrics namespaces
METRICS_NAMESPACE = "chat_stream_pipeline"
ERROR_KIND_PARSE = "parse_error"
ERROR_KIND_NOT_OBJECT = "not_json_object"
ERROR_KIND_UNROUTABLE = "unroutable"

# Default order lifecycle stages used by the sample generator
ORDER_STAGES: tuple[str, ...] = (
    "ACCEPTED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    "IN_TRANSIT",
    "PROCESSING",
    "DELAYED",
    "OUT_FOR_DELIVERY",
    "RETURNED",
    "AWAITING_PICKUP",
    "ARRIVED",
    "FAILED",
    "PENDING",
    "ON_ROUTE",
    "DELIVERED",
)

SENDER_APP_TYPES: tuple[str, ...] = ("Courier Android", "Customer iOS")

# ISO-like cities for demo enrichment rows
CITY_CODES: tuple[str, ...] = (
    "BCN",
    "NYC",
    "LON",
    "PAR",
    "BER",
    "TOK",
    "ROM",
    "MAD",
    "SYD",
    "MEX",
    "CAI",
    "AMS",
    "TOR",
    "IST",
    "SAN",
    "SIN",
    "RIO",
    "BUE",
    "CPT",
    "MUM",
)
