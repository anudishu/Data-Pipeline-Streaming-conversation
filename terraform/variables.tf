variable "project_id" {
  description = "The ID of the Google Cloud project"
  type        = string
}

variable "region" {
  description = "The region for the resources"
  type        = string
}

variable "zone" {
  description = "The zone for the resources"
  type        = string
}

variable "bucket_name" {
  description = "The name of the GCS bucket"
  type        = string
}

variable "topic_name" {
  description = "The name of the Pub/Sub topic"
  type        = string
  default     = "topic-conversation"
}

variable "subscription_name" {
  description = "The name of the Pub/Sub subscription"
  type        = string
  default     = "submessages"
}

variable "dataset_id" {
  description = "The ID of the BigQuery dataset"
  type        = string
}

variable "table_conversations_name" {
  description = "The name of the BigQuery conversations table"
  type        = string
  default     = "conversations"
}

variable "table_orders_name" {
  description = "The name of the BigQuery orders table"
  type        = string
  default     = "orders"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner_label" {
  type    = string
  default = "data-eng"
}

variable "enable_project_apis" {
  type    = bool
  default = true
}

variable "pipeline_service_account_id" {
  type    = string
  default = "streaming-pipeline-sa"
}

variable "dead_letter_topic_name" {
  type     = string
  default  = null
  nullable = true
}

variable "bucket_temp_cleanup_age_days" {
  type    = number
  default = 14
}

variable "bucket_soft_delete_retention_seconds" {
  type    = number
  default = 604800
}

variable "pubsub_ack_deadline_seconds" {
  type    = number
  default = 20
}

variable "pubsub_retry_minimum_backoff" {
  type    = string
  default = "10s"
}

variable "pubsub_retry_maximum_backoff" {
  type    = string
  default = "600s"
}

variable "pubsub_max_delivery_attempts" {
  type    = number
  default = 10
}

variable "create_dead_letter_subscription" {
  type    = bool
  default = true
}

variable "dead_letter_subscription_name" {
  type    = string
  default = "submessages-dlq-audit"
}

variable "dead_letter_sub_ack_deadline_seconds" {
  type    = number
  default = 60
}

variable "dead_letter_sub_message_retention_duration" {
  type    = string
  default = "604800s"
}
