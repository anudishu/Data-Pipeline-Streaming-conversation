resource "google_project_service" "enabled_apis" {
  for_each = var.enable_project_apis ? toset([
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "dataflow.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]) : toset([])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
