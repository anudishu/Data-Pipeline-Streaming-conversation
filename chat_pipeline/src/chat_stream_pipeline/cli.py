"""CLI entrypoint for launching the Beam streaming job."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from chat_stream_pipeline.beam_pipeline import describe_graph, run_streaming_pipeline
from chat_stream_pipeline.config import parse_pipeline_settings
from chat_stream_pipeline.logging_utils import setup_logging


def main(argv: Optional[list[str]] = None) -> int:
    setup_logging()
    log = logging.getLogger("chat_stream_pipeline.cli")
    settings = parse_pipeline_settings(argv)
    log.info("%s", describe_graph(settings))
    try:
        run_streaming_pipeline(settings)
    except KeyboardInterrupt:
        log.warning("Interrupted by user")
        return 130
    except Exception:
        log.exception("Pipeline failed to start or crashed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
