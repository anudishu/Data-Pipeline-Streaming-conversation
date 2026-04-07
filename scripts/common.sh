#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

log() {
  printf '%s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" 1>&2
}

die() {
  printf 'ERROR: %s\n' "$*" 1>&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"
}

need_file() {
  [[ -f "$1" ]] || die "Missing file: $1"
}

need_dir() {
  [[ -d "$1" ]] || die "Missing directory: $1"
}

load_tfvars() {
  # Loads a terraform.tfvars file into env vars (simple key="value" parsing).
  # It intentionally supports only string values; keep it predictable.
  local tfvars="$1"
  need_file "$tfvars"

  while IFS= read -r line; do
    [[ -z "${line// /}" ]] && continue
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue

    if [[ "${line}" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"(.*)\"[[:space:]]*$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local val="${BASH_REMATCH[2]}"
      export "${key}=${val}"
    fi
  done <"$tfvars"
}

terraform_output() {
  local tf_dir="$1"
  need_dir "$tf_dir"
  (cd "$tf_dir" && terraform output -json 2>/dev/null || true)
}

json_get() {
  # Usage: json_get '<json>' '.path.to.value'
  local json="$1"
  local jq_expr="$2"
  printf '%s' "$json" | jq -r "$jq_expr"
}

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || die "Required env var not set: ${name}"
}

print_next_steps() {
  cat <<'EOF'

Next steps:
- Start the streaming Dataflow pipeline: scripts/run_pipeline.sh
- Publish sample events:               scripts/publish_sample.sh
- Validate results in BigQuery:        scripts/validate.sh
- Optional health snapshot:            scripts/health_check.sh

EOF
}

