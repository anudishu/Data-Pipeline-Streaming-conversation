#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.sh"

need_cmd terraform

TF_DIR="${REPO_ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

need_dir "${TF_DIR}"

if [[ -f "${TFVARS}" ]]; then
  load_tfvars "${TFVARS}"
  if [[ -n "${project_id:-}" ]]; then
    log "Project from tfvars: ${project_id}"
  fi
fi

log "Destroying Terraform resources..."
(cd "${TF_DIR}" && terraform destroy -auto-approve)
log "Done."

