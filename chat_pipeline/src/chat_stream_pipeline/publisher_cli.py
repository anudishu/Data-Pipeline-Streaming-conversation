"""Publish newline-delimited JSON from GCS to Pub/Sub with retries and logging."""

from __future__ import annotations

import logging
import sys
import time
from typing import Iterator, Optional

from google.api_core import exceptions as gcloud_exceptions
from google.cloud import pubsub_v1, storage

from chat_stream_pipeline.config import parse_publisher_settings
from chat_stream_pipeline.logging_utils import setup_logging


def iter_gcs_jsonl_lines(bucket_name: str, object_name: str) -> Iterator[str]:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    with blob.open("r", encoding="utf-8") as handle:
        for line in handle:
            yield line.rstrip("\n")


def publish_lines(
    project: str,
    topic: str,
    lines: Iterator[str],
    sleep_seconds: float,
    dry_run: bool,
) -> tuple[int, int]:
    """
    Publish non-blank lines to Pub/Sub.

    Returns:
        (published_count, skipped_blank_count)
    """

    log = logging.getLogger("chat_stream_pipeline.publisher")
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)

    if not dry_run:
        try:
            publisher.get_topic(request={"topic": topic_path})
        except gcloud_exceptions.NotFound as exc:
            log.error("Topic not found: %s (%s)", topic_path, exc)
            raise

    published = 0
    skipped = 0
    for line in lines:
        if line.strip() == "":
            skipped += 1
            continue
        payload = line.encode("utf-8")
        if dry_run:
            published += 1
            log.debug("dry_run would publish %s bytes", len(payload))
            time.sleep(sleep_seconds)
            continue

        for attempt in range(5):
            try:
                future = publisher.publish(topic_path, data=payload)
                future.result(timeout=60)
                published += 1
                break
            except (gcloud_exceptions.GoogleAPIError, TimeoutError) as exc:
                wait = min(2**attempt, 30)
                log.warning("Publish attempt %s failed (%s); retry in %ss", attempt + 1, exc, wait)
                time.sleep(wait)
        else:
            log.error("Giving up on line after repeated failures")
            raise RuntimeError("pubsub_publish_failed")

        time.sleep(sleep_seconds)

    return published, skipped


def main(argv: Optional[list[str]] = None) -> int:
    setup_logging()
    log = logging.getLogger("chat_stream_pipeline.publisher")
    settings = parse_publisher_settings(argv)

    if settings.dry_run:
        log.info("Dry run enabled; reading GCS object without publishing")

    def line_source() -> Iterator[str]:
        yield from iter_gcs_jsonl_lines(settings.bucket, settings.object_name)

    try:
        published, skipped = publish_lines(
            settings.project,
            settings.topic,
            line_source(),
            settings.sleep_seconds,
            settings.dry_run,
        )
    except Exception:
        log.exception("Publisher failed")
        return 1

    log.info("Published %s messages (skipped_blank=%s)", published, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
