#!/usr/bin/env python3
"""Publish JSONL from GCS to Pub/Sub (library entrypoint in ``chat_stream_pipeline.publisher_cli``)."""

from __future__ import annotations

import sys

from chat_stream_pipeline.publisher_cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
