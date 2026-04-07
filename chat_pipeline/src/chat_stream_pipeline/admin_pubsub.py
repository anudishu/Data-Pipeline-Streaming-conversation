"""Idempotent Pub/Sub topic and subscription provisioning for lab environments."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from google.api_core import exceptions as gcloud_exceptions
from google.cloud import pubsub_v1

from chat_stream_pipeline.logging_utils import setup_logging


def ensure_topic(publisher: pubsub_v1.PublisherClient, project: str, topic: str) -> str:
    path = publisher.topic_path(project, topic)
    try:
        publisher.create_topic(request={"name": path})
        logging.getLogger("chat_stream_pipeline.admin").info("Created topic %s", path)
    except gcloud_exceptions.AlreadyExists:
        logging.getLogger("chat_stream_pipeline.admin").debug("Topic already exists %s", path)
    return path


def ensure_subscription(
    subscriber: pubsub_v1.SubscriberClient,
    project: str,
    subscription: str,
    topic_path: str,
) -> str:
    path = subscriber.subscription_path(project, subscription)
    try:
        subscriber.create_subscription(request={"name": path, "topic": topic_path})
        logging.getLogger("chat_stream_pipeline.admin").info("Created subscription %s", path)
    except gcloud_exceptions.AlreadyExists:
        logging.getLogger("chat_stream_pipeline.admin").debug("Subscription already exists %s", path)
    return path


def build_admin_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create Pub/Sub topic + subscription if missing.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--subscription", required=True)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    setup_logging()
    log = logging.getLogger("chat_stream_pipeline.admin")
    args = build_admin_parser().parse_args(argv)

    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    try:
        topic_path = ensure_topic(publisher, args.project, args.topic)
        sub_path = ensure_subscription(subscriber, args.project, args.subscription, topic_path)
    except gcloud_exceptions.GoogleAPIError:
        log.exception("Pub/Sub admin operation failed")
        return 1

    print(topic_path)
    print(sub_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
