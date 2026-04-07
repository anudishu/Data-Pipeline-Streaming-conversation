resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = "dt_chat"
  location                    = "US"
  default_table_expiration_ms = null
  delete_contents_on_destroy  = true
  labels                      = local.labels

  depends_on = [google_project_service.enabled_apis]
}

resource "google_bigquery_table" "conversations" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = var.table_conversations_name

  description = "Courier/customer chat messages keyed by order and customer identifiers."

  time_partitioning {
    type  = "DAY"
    field = "messageSentTime"
  }

  clustering = ["orderId", "senderAppType"]

  schema = <<EOF
[
  {
    "name": "senderAppType",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "courierId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "fromId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "toId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "chatStartedByMessage",
    "type": "BOOLEAN",
    "mode": "NULLABLE"
  },
  {
    "name": "orderId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "orderStage",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "customerId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "messageSentTime",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "orders" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = var.table_orders_name

  description = "Order header enrichment rows (city code) keyed by orderId."

  clustering = ["orderId", "cityCode"]

  lifecycle {
    prevent_destroy = false
  }

  schema = <<EOF
[
  {
    "name": "cityCode",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "orderId",
    "type": "INTEGER",
    "mode": "NULLABLE"
  }
]
EOF
}
