#!/usr/bin/env bash
set -euo pipefail

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 127
  }
}

project_id() {
  if [[ -n "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
    echo "${GOOGLE_CLOUD_PROJECT}"
    return
  fi
  gcloud config get-value project 2>/dev/null
}

timestamp() {
  date -u +"%Y-%m-%dT%H-%M-%SZ"
}

ensure_prereqs() {
  need_cmd gcloud
  need_cmd jq
  need_cmd rg
  local project
  project="$(project_id)"
  if [[ -z "$project" || "$project" == "(unset)" ]]; then
    echo "No project configured. Set GOOGLE_CLOUD_PROJECT or run: gcloud config set project <PROJECT_ID>" >&2
    exit 2
  fi
}

out_dir() {
  echo "docs/google/_inventory"
}
