resource "google_pubsub_subscription" "dead_letter_audit" {
  count = var.create_dead_letter_subscription ? 1 : 0

  name  = var.dead_letter_subscription_name
  topic = google_pubsub_topic.subscription_dead_letter.name

  ack_deadline_seconds       = var.dead_letter_sub_ack_deadline_seconds
  enable_message_ordering    = false
  retain_acked_messages      = false
  message_retention_duration = var.dead_letter_sub_message_retention_duration

  expiration_policy {
    ttl = ""
  }

  retry_policy {
    minimum_backoff = var.pubsub_retry_minimum_backoff
    maximum_backoff = var.pubsub_retry_maximum_backoff
  }

  labels = merge(
    local.labels,
    {
      role = "dead-letter-audit"
    },
  )

  depends_on = [
    google_project_service.enabled_apis,
    google_pubsub_topic.subscription_dead_letter,
  ]
}
