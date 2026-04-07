#!/usr/bin/env python3
"""
Create a Pub/Sub topic and subscription if they do not exist.

Prefer Terraform for production; this script is useful for quick labs.
"""

from __future__ import annotations

import sys

from chat_stream_pipeline.admin_pubsub import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
