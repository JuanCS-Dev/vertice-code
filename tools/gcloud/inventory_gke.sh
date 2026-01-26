#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tools/gcloud/_lib.sh
source "${SCRIPT_DIR}/_lib.sh"

ensure_prereqs

PROJECT="$(project_id)"
TS="$(timestamp)"
OUT="$(out_dir)"
mkdir -p "${OUT}"

FILE="${OUT}/gke_clusters_${PROJECT}_${TS}.json"
gcloud container clusters list --project "${PROJECT}" --format=json | jq '.' >"${FILE}"
echo "Wrote ${FILE}"

SUMMARY="${OUT}/gke_clusters_${PROJECT}_summary_${TS}.md"
{
  echo "# GKE inventory (${PROJECT})"
  echo
  echo "- Timestamp (UTC): ${TS}"
  echo
  echo "## Clusters"
  echo
  echo "| Location | Name | Status | Master version | Node version |"
  echo "|---|---|---|---|---|"
  jq -r '
    .[]
    | [
        (.location // "-"),
        (.name // "-"),
        (.status // "-"),
        (.currentMasterVersion // "-"),
        (.currentNodeVersion // "-")
      ]
    | @tsv
  ' "${FILE}" | while IFS=$'\t' read -r location name status master_version node_version; do
    printf "| %s | %s | %s | %s | %s |\n" "${location}" "${name}" "${status}" "${master_version}" "${node_version}"
  done
} >"${SUMMARY}"
echo "Wrote ${SUMMARY}"
