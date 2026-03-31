#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd python3
need_cmd gcloud

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

need_dir "${TF_DIR}"
need_file "${TFVARS}"
need_file "${TF_DIR}/send-data-to-pubsub.py"

load_tfvars "${TFVARS}"
require_env project_id
require_env bucket_name
require_env topic_name

gcloud config set project "${project_id}" >/dev/null

SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
OBJECT_NAME="${OBJECT_NAME:-conversations.json}"

log "Publishing sample events to Pub/Sub"
log "  project: ${project_id}"
log "  topic:   ${topic_name}"
log "  bucket:  ${bucket_name}"
log "  object:  ${OBJECT_NAME}"
log "  sleep:   ${SLEEP_SECONDS}s"

(
  cd "${TF_DIR}"
  if [[ -f ".venv/bin/activate" ]]; then
    # Prefer the same venv used for the pipeline if present.
    source .venv/bin/activate
  fi
  python send-data-to-pubsub.py \
    --project "${project_id}" \
    --topic "${topic_name}" \
    --bucket "${bucket_name}" \
    --object "${OBJECT_NAME}" \
    --sleep_seconds "${SLEEP_SECONDS}"
)

