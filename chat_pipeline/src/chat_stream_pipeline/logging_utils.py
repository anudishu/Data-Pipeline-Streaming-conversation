"""Structured logging defaults for CLIs and operators."""

from __future__ import annotations

import logging
import os
from typing import Optional


def setup_logging(level: Optional[int] = None) -> None:
    """Configure root logging once (idempotent for repeated CLI invocations)."""

    if level is None:
        env = os.environ.get("CHAT_PIPELINE_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env, logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
