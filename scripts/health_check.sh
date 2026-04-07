#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd python3
need_cmd gcloud

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"
VENV_DIR="${TF_DIR}/.venv"

need_dir "${TF_DIR}"
need_file "${TFVARS}"

load_tfvars "${TFVARS}"
require_env project_id
require_env dataset_id
require_env subscription_name

gcloud config set project "${project_id}" >/dev/null

if [[ -f "${VENV_DIR}/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
fi

log "Running operational health checks (Pub/Sub + BigQuery)..."
python -m chat_stream_pipeline.health \
  --project "${project_id}" \
  --subscription "${subscription_name}" \
  --dataset_id "${dataset_id}"
