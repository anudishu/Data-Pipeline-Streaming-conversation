#------ Terraform Provider---------#
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.27.0"
    }
  }
}

#------ Google Provider---------#
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

#------ Storage bucket and sample object ---------#
resource "google_storage_bucket" "streaming_project_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  labels                      = local.labels

  soft_delete_policy {
    retention_duration_seconds = var.bucket_soft_delete_retention_seconds
  }

  lifecycle_rule {
    action {
      type = "AbortIncompleteMultipartUpload"
    }
    condition {
      age = 1
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age            = var.bucket_temp_cleanup_age_days
      matches_prefix = ["temp/", "staging/"]
    }
  }

  lifecycle {
    prevent_destroy = false
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_storage_bucket_object" "conversations_json" {
  name   = "conversations.json"
  bucket = google_storage_bucket.streaming_project_bucket.name
  source = "conversations.json"

  lifecycle {
    prevent_destroy = false
  }

}

#------ Pub/Sub ---------#
resource "google_pubsub_topic" "topic" {
  name = var.topic_name

  message_storage_policy {
    allowed_persistence_regions = [var.region]
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_pubsub_topic" "subscription_dead_letter" {
  name = local.dead_letter_topic

  message_storage_policy {
    allowed_persistence_regions = [var.region]
  }

  depends_on = [google_project_service.enabled_apis]
}

resource "google_pubsub_subscription" "subscription" {
  name  = var.subscription_name
  topic = google_pubsub_topic.topic.name

  ack_deadline_seconds = var.pubsub_ack_deadline_seconds

  retry_policy {
    minimum_backoff = var.pubsub_retry_minimum_backoff
    maximum_backoff = var.pubsub_retry_maximum_backoff
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.subscription_dead_letter.id
    max_delivery_attempts = var.pubsub_max_delivery_attempts
  }

  expiration_policy {
    ttl = ""
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_pubsub_topic.subscription_dead_letter,
  ]
}
