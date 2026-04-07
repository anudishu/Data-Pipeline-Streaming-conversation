# Dedicated topic for pipeline-level parse failures and unroutable JSON (application DLQ).

resource "google_pubsub_topic" "pipeline_parse_errors" {
  name = local.pipeline_parse_errors_topic

  message_storage_policy {
    allowed_persistence_regions = [var.region]
  }

  labels = merge(
    local.labels,
    {
      role = "pipeline-parse-errors"
    },
  )

  depends_on = [google_project_service.enabled_apis]
}

resource "google_pubsub_topic_iam_member" "pipeline_parse_errors_publisher" {
  topic  = google_pubsub_topic.pipeline_parse_errors.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [
    google_project_service.enabled_apis,
    google_pubsub_topic.pipeline_parse_errors,
    google_service_account.pipeline,
  ]
}
