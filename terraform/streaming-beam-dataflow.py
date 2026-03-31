import apache_beam as beam
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import WriteToBigQuery
import json
from apache_beam.options.pipeline_options import PipelineOptions
import argparse

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Streaming Pub/Sub -> BigQuery pipeline (Apache Beam).")
    parser.add_argument("--subscription", required=True, help="Pub/Sub subscription path: projects/<p>/subscriptions/<s>")
    parser.add_argument("--bq_conversations_table", required=True, help="<project>:<dataset>.<table>")
    parser.add_argument("--bq_orders_table", required=True, help="<project>:<dataset>.<table>")
    parser.add_argument(
        "--runner",
        default="DirectRunner",
        choices=["DirectRunner", "DataflowRunner"],
        help="Execution runner. Use DataflowRunner for managed Dataflow.",
    )
    parser.add_argument("--project", default=None, help="GCP project for the runner (recommended for DataflowRunner).")
    parser.add_argument("--region", default=None, help="GCP region (required for DataflowRunner).")
    parser.add_argument("--temp_location", default=None, help="GCS temp location, e.g. gs://<bucket>/temp")
    parser.add_argument("--staging_location", default=None, help="GCS staging location, e.g. gs://<bucket>/staging")
    parser.add_argument("--job_name", default=None, help="Dataflow job name (DataflowRunner only).")
    return parser.parse_args()


args = _parse_args()

pipeline_args = [
    f"--runner={args.runner}",
    "--streaming",
]
if args.project:
    pipeline_args.append(f"--project={args.project}")
if args.region:
    pipeline_args.append(f"--region={args.region}")
if args.temp_location:
    pipeline_args.append(f"--temp_location={args.temp_location}")
if args.staging_location:
    pipeline_args.append(f"--staging_location={args.staging_location}")
if args.job_name:
    pipeline_args.append(f"--job_name={args.job_name}")

options = PipelineOptions(pipeline_args)

#Define your Beam pipeline
with beam.Pipeline(options=options) as pipeline:
    #Read the input data from Pub/Sub
    messages = pipeline | ReadFromPubSub(subscription=args.subscription)

    #Parse the JSON messages
    parsed_messages = messages | beam.Map(lambda msg: json.loads(msg))

    #Extract the desired fields for 'conversations' table
    conversations_data = parsed_messages | beam.Map(lambda data: {
        'senderAppType': data.get('senderAppType', 'N/A'),
        'courierId': data.get('courierId', None),
        'fromId': data.get('fromId', None),
        'toId': data.get('toId', None),
        'chatStartedByMessage': data.get('chatStartedByMessage', False),
        'orderId': data.get('orderId', None),
        'orderStage': data.get('orderStage', 'N/A'),
        'customerId': data.get('customerId', None),
        'messageSentTime': data.get('messageSentTime', None),
        #only elements with both fields present are processed further in the pipeline
    }) | beam.Filter(lambda data: data['orderId'] is not None and data['customerId'] is not None)

    #Extract the desired fields for 'orders' table
    orders_data = parsed_messages | beam.Map(lambda data: {
        'cityCode': data.get('cityCode', 'N/A'),
        'orderId': data.get('orderId', None),
        #only elements that satisfy both conditions (non-None 'orderId' and 'cityCode' not equal to 'N/A') will pass through the filter and continue to the subsequent steps in the pipeline
    }) | beam.Filter(lambda data: data['orderId'] is not None and data['cityCode'] != 'N/A')

    #Define the schema for the 'conversations' table
    conversations_schema = {
        'fields': [
            {'name': 'senderAppType', 'type': 'STRING'},
            {'name': 'courierId', 'type': 'INTEGER'},
            {'name': 'fromId', 'type': 'INTEGER'},
            {'name': 'toId', 'type': 'INTEGER'},
            {'name': 'chatStartedByMessage', 'type': 'BOOLEAN'},
            {'name': 'orderId', 'type': 'INTEGER'},
            {'name': 'orderStage', 'type': 'STRING'},
            {'name': 'customerId', 'type': 'INTEGER'},
            {'name': 'messageSentTime', 'type': 'TIMESTAMP'}
        ]
    }

    #Define the schema for the 'orders' table
    orders_schema = {
        'fields': [
            {'name': 'cityCode', 'type': 'STRING'},
            {'name': 'orderId', 'type': 'INTEGER'}
        ]
    }

    #Write the conversations data to the 'conversations' table in BigQuery
    conversations_data | 'Write conversations to BigQuery' >> WriteToBigQuery(
        table=args.bq_conversations_table,
        schema=conversations_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
    )

    #Write the orders data to the 'orders' table in BigQuery
    orders_data | 'Write orders to BigQuery' >> WriteToBigQuery(
        table=args.bq_orders_table,
        schema=orders_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
    )
