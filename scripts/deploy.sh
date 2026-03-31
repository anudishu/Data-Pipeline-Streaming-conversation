#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd gcloud
need_cmd terraform
need_cmd jq

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

need_dir "${TF_DIR}"
need_file "${TFVARS}"

log "Loading ${TFVARS}"
load_tfvars "${TFVARS}"

require_env project_id

log "Using GCP project: ${project_id}"
gcloud config set project "${project_id}" >/dev/null

log "Deploying Terraform resources..."
(cd "${TF_DIR}" && terraform init -upgrade)
(cd "${TF_DIR}" && terraform apply -auto-approve)

log ""
log "Terraform outputs:"
(cd "${TF_DIR}" && terraform output)

print_next_steps

