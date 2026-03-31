output "bucket_name" {
  value       = google_storage_bucket.streaming_project_bucket.name
  description = "GCS bucket used for staging/temp and sample data."
}

output "pubsub_topic" {
  value       = google_pubsub_topic.topic.name
  description = "Pub/Sub topic name."
}

output "pubsub_subscription" {
  value       = google_pubsub_subscription.subscription.name
  description = "Pub/Sub subscription name."
}

output "bigquery_dataset" {
  value       = google_bigquery_dataset.dataset.dataset_id
  description = "BigQuery dataset id."
}

output "bigquery_conversations_table" {
  value       = google_bigquery_table.conversations.table_id
  description = "BigQuery conversations table id."
}

output "bigquery_orders_table" {
  value       = google_bigquery_table.orders.table_id
  description = "BigQuery orders table id."
}

