#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd python3
need_cmd gcloud
need_cmd terraform
need_cmd jq

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"
VENV_DIR="${TF_DIR}/.venv"

need_dir "${TF_DIR}"
need_file "${TFVARS}"
need_file "${TF_DIR}/requirements.txt"
need_file "${TF_DIR}/streaming-beam-dataflow.py"

log "Loading ${TFVARS}"
load_tfvars "${TFVARS}"

require_env project_id
require_env region
require_env bucket_name
require_env dataset_id
require_env subscription_name

gcloud config set project "${project_id}" >/dev/null

log "Creating venv (if missing) at ${VENV_DIR}"
if [[ ! -d "${VENV_DIR}" ]]; then
  (cd "${TF_DIR}" && python3 -m venv .venv)
fi

log "Installing Python dependencies"
(
  cd "${TF_DIR}"
  source .venv/bin/activate
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
)

SUB_PATH="projects/${project_id}/subscriptions/${subscription_name}"
CONV_TABLE="${project_id}:${dataset_id}.conversations"
ORD_TABLE="${project_id}:${dataset_id}.orders"

JOB_NAME="streaming-chat-$(date +%Y%m%d-%H%M%S)"

PIPELINE_SA="$(cd "${TF_DIR}" && terraform output -raw pipeline_service_account_email)"

log ""
log "Starting streaming pipeline on Dataflow:"
log "  subscription: ${SUB_PATH}"
log "  conversations: ${CONV_TABLE}"
log "  orders:        ${ORD_TABLE}"
log "  job_name:      ${JOB_NAME}"
log "  sa:            ${PIPELINE_SA}"
log ""

(
  cd "${TF_DIR}"
  source .venv/bin/activate
  python streaming-beam-dataflow.py \
    --runner DataflowRunner \
    --project "${project_id}" \
    --region "${region}" \
    --temp_location "gs://${bucket_name}/temp" \
    --staging_location "gs://${bucket_name}/staging" \
    --subscription "${SUB_PATH}" \
    --bq_conversations_table "${CONV_TABLE}" \
    --bq_orders_table "${ORD_TABLE}" \
    --job_name "${JOB_NAME}" \
    --service_account_email "${PIPELINE_SA}"
)

