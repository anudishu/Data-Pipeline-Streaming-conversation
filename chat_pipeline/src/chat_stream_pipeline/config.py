"""Pipeline and tooling configuration (CLI arguments mapped to structured settings)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PipelineSettings:
    """Immutable settings for the Apache Beam streaming job."""

    subscription: str
    bq_conversations_table: str
    bq_orders_table: str
    runner: str
    project: Optional[str]
    region: Optional[str]
    temp_location: Optional[str]
    staging_location: Optional[str]
    job_name: Optional[str]
    service_account_email: Optional[str]
    errors_topic: Optional[str]

    def pipeline_options_argv(self) -> list[str]:
        """Build argv fragments consumed by ``apache_beam.options.pipeline_options.PipelineOptions``."""

        args: list[str] = [
            f"--runner={self.runner}",
            "--streaming",
        ]
        if self.project:
            args.append(f"--project={self.project}")
        if self.region:
            args.append(f"--region={self.region}")
        if self.temp_location:
            args.append(f"--temp_location={self.temp_location}")
        if self.staging_location:
            args.append(f"--staging_location={self.staging_location}")
        if self.job_name:
            args.append(f"--job_name={self.job_name}")
        if self.service_account_email:
            args.append(f"--service_account_email={self.service_account_email}")
        return args


def build_pipeline_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Streaming Pub/Sub → BigQuery pipeline (Apache Beam).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--subscription",
        required=True,
        help="Pub/Sub subscription path: projects/<p>/subscriptions/<s>",
    )
    parser.add_argument(
        "--bq_conversations_table",
        required=True,
        help="Destination table for conversation rows: <project>:<dataset>.<table>",
    )
    parser.add_argument(
        "--bq_orders_table",
        required=True,
        help="Destination table for order enrichment rows: <project>:<dataset>.<table>",
    )
    parser.add_argument(
        "--runner",
        default="DirectRunner",
        choices=["DirectRunner", "DataflowRunner"],
        help="Beam runner. Use DataflowRunner for managed Dataflow.",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP project id for the runner (recommended for DataflowRunner).",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="GCP region (required for DataflowRunner).",
    )
    parser.add_argument(
        "--temp_location",
        default=None,
        help="GCS temp location, e.g. gs://<bucket>/temp",
    )
    parser.add_argument(
        "--staging_location",
        default=None,
        help="GCS staging location, e.g. gs://<bucket>/staging",
    )
    parser.add_argument(
        "--job_name",
        default=None,
        help="Dataflow job name (DataflowRunner only).",
    )
    parser.add_argument(
        "--service_account_email",
        default=None,
        help="Worker service account email (DataflowRunner).",
    )
    parser.add_argument(
        "--errors_topic",
        default=None,
        help=(
            "Optional Pub/Sub topic (full path projects/p/topics/t) for JSON parse failures "
            "and unroutable records. When omitted, errors are counted only (no Pub/Sub sink)."
        ),
    )
    return parser


def parse_pipeline_settings(argv: Optional[list[str]] = None) -> PipelineSettings:
    parser = build_pipeline_arg_parser()
    args = parser.parse_args(argv)
    return PipelineSettings(
        subscription=args.subscription,
        bq_conversations_table=args.bq_conversations_table,
        bq_orders_table=args.bq_orders_table,
        runner=args.runner,
        project=args.project,
        region=args.region,
        temp_location=args.temp_location,
        staging_location=args.staging_location,
        job_name=args.job_name,
        service_account_email=args.service_account_email,
        errors_topic=args.errors_topic,
    )


@dataclass(frozen=True)
class PublisherSettings:
    project: str
    topic: str
    bucket: str
    object_name: str
    sleep_seconds: float
    dry_run: bool


def build_publisher_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish newline-delimited JSON from GCS to Pub/Sub.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--project", required=True, help="GCP project id")
    parser.add_argument("--topic", required=True, help="Pub/Sub topic id (short name, not full path)")
    parser.add_argument("--bucket", required=True, help="GCS bucket containing the object")
    parser.add_argument(
        "--object",
        dest="object_name",
        default="conversations.json",
        help="GCS object name",
    )
    parser.add_argument(
        "--sleep_seconds",
        type=float,
        default=1.0,
        help="Delay between publishes (seconds)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Read and validate lines locally without publishing",
    )
    return parser


def parse_publisher_settings(argv: Optional[list[str]] = None) -> PublisherSettings:
    parser = build_publisher_arg_parser()
    args = parser.parse_args(argv)
    return PublisherSettings(
        project=args.project,
        topic=args.topic,
        bucket=args.bucket,
        object_name=args.object_name,
        sleep_seconds=args.sleep_seconds,
        dry_run=args.dry_run,
    )


@dataclass(frozen=True)
class HealthCheckSettings:
    project: str
    subscription: str
    dataset_id: str
    conversations_table: str
    orders_table: str
    sample_limit: int


def build_health_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lightweight health checks for Pub/Sub backlog and BigQuery row presence.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--subscription", required=True, help="Short subscription id")
    parser.add_argument("--dataset_id", required=True)
    parser.add_argument("--conversations_table", default="conversations")
    parser.add_argument("--orders_table", default="orders")
    parser.add_argument("--sample_limit", type=int, default=5)
    return parser


def parse_health_settings(argv: Optional[list[str]] = None) -> HealthCheckSettings:
    parser = build_health_arg_parser()
    args = parser.parse_args(argv)
    return HealthCheckSettings(
        project=args.project,
        subscription=args.subscription,
        dataset_id=args.dataset_id,
        conversations_table=args.conversations_table,
        orders_table=args.orders_table,
        sample_limit=args.sample_limit,
    )
