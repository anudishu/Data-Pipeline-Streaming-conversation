from google.cloud import pubsub_v1
from google.cloud import storage
import time
import argparse


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish newline-delimited JSON from GCS to Pub/Sub.")
    parser.add_argument("--project", required=True, help="GCP project id")
    parser.add_argument("--topic", required=True, help="Pub/Sub topic name (not full path)")
    parser.add_argument("--bucket", required=True, help="GCS bucket name containing the input object")
    parser.add_argument("--object", default="conversations.json", help="GCS object name (default: conversations.json)")
    parser.add_argument("--sleep_seconds", type=float, default=1.0, help="Delay between messages (default: 1.0)")
    return parser.parse_args()


args = _parse_args()

#Create a publisher client
publisher = pubsub_v1.PublisherClient()
#Specify the topic path
topic_path = publisher.topic_path(args.project, args.topic)

#Get the topic
topic = publisher.get_topic(request={"topic": topic_path})
#Check if the topic exists
if topic is None:
    print('Topic does not exist:', topic_path)
    exit()

#Create a storage client
storage_client = storage.Client()

#Specify the bucket and file names
bucket_name = args.bucket
file_name = args.object

#Get the bucket and blob
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(file_name)

#Read the file line by line
with blob.open("r") as f_in:
    for line in f_in:
        #Data must be a bytestring
        data = line.encode('utf-8')
        #Publish the data to the topic
        future = publisher.publish(topic=topic.name, data=data)
        print(future.result())
        #Sleep for 1 second before publishing the next message
        time.sleep(args.sleep_seconds)
