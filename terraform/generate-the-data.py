#!/usr/bin/env python3
"""Generate synthetic JSONL for demos (see ``chat_stream_pipeline.data_generator``)."""

from __future__ import annotations

import sys

from chat_stream_pipeline.data_generator import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
