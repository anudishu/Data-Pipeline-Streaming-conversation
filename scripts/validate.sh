#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd bq
need_cmd gcloud

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

need_dir "${TF_DIR}"
need_file "${TFVARS}"
need_file "${TF_DIR}/create-view.sql"

load_tfvars "${TFVARS}"
require_env project_id
require_env dataset_id

gcloud config set project "${project_id}" >/dev/null

log "Checking BigQuery tables for recent rows..."

CONV_TABLE="${project_id}:${dataset_id}.conversations"
ORD_TABLE="${project_id}:${dataset_id}.orders"

log ""
log "Conversations table sample (last 10 rows): ${CONV_TABLE}"
bq query --use_legacy_sql=false --format=prettyjson \
  "SELECT * FROM \`${project_id}.${dataset_id}.conversations\` ORDER BY messageSentTime DESC LIMIT 10"

log ""
log "Orders table sample (last 10 rows): ${ORD_TABLE}"
bq query --use_legacy_sql=false --format=prettyjson \
  "SELECT * FROM \`${project_id}.${dataset_id}.orders\` ORDER BY orderId DESC LIMIT 10"

if [[ "${CREATE_VIEW:-1}" == "1" ]]; then
  log ""
  log "Creating/refreshing analytics view..."
  sed -e "s/YOUR_PROJECT_ID/${project_id}/g" -e "s/YOUR_DATASET/${dataset_id}/g" "${TF_DIR}/create-view.sql" | \
    bq query --use_legacy_sql=false >/dev/null

  log "View created: ${project_id}.${dataset_id}.customer_courier_conversations_view"

  log ""
  log "View sample (last 10 orders):"
  bq query --use_legacy_sql=false --format=prettyjson \
    "SELECT * FROM \`${project_id}.${dataset_id}.customer_courier_conversations_view\` ORDER BY last_message_time DESC LIMIT 10"
else
  warn "Skipping view creation (CREATE_VIEW=0)."
fi

