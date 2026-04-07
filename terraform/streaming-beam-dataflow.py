#!/usr/bin/env python3
"""Thin wrapper: install the editable package (see requirements.txt) then run the Beam CLI."""

from __future__ import annotations

import sys

from chat_stream_pipeline.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
