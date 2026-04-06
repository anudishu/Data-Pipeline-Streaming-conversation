resource "google_service_account" "pipeline" {
  account_id   = var.pipeline_service_account_id
  display_name = "Streaming pipeline runtime"
  description  = "Runs Dataflow and reads Pub/Sub in this workspace."

  depends_on = [google_project_service.enabled_apis]
}

resource "google_project_iam_member" "pipeline_project_roles" {
  for_each = toset([
    "roles/dataflow.worker",
    "roles/pubsub.subscriber",
    "roles/bigquery.jobUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [google_project_service.enabled_apis]
}

resource "google_storage_bucket_iam_member" "pipeline_bucket_admin" {
  bucket = google_storage_bucket.streaming_project_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [
    google_project_service.enabled_apis,
    google_service_account.pipeline,
  ]
}

resource "google_bigquery_dataset_iam_member" "pipeline_dataset_editor" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [
    google_project_service.enabled_apis,
    google_bigquery_dataset.dataset,
    google_service_account.pipeline,
  ]
}
