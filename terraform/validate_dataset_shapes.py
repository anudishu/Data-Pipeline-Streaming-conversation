#!/usr/bin/env python3
"""Validate bundled JSONL shapes (implementation lives in ``chat_stream_pipeline.validate``)."""

from __future__ import annotations

import sys

from chat_stream_pipeline.validate import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
