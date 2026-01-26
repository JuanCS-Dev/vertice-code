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

regions_from_assets() {
  gcloud asset search-all-resources \
    --scope="projects/${PROJECT}" \
    --asset-types="cloudfunctions.googleapis.com/Function" \
    --format=json 2>/dev/null \
    | jq -r '.[].location' \
    | rg -v '^(global|-)$' \
    | sort -u
}

regions_from_env_or_config() {
  if [[ -n "${REGIONS:-}" ]]; then
    echo "${REGIONS}" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | rg -v '^$' | sort -u
    return
  fi

  {
    gcloud config get-value functions/region 2>/dev/null || true
    gcloud config get-value compute/region 2>/dev/null || true
    echo "us-central1"
  } | rg -v '^(\\(unset\\)|-)$' | sort -u
}

REGIONS="$(regions_from_assets || true)"
if [[ -z "${REGIONS}" ]]; then
  REGIONS="$(regions_from_env_or_config)"
fi

echo "${REGIONS}" | while read -r REGION; do
  [[ -z "${REGION}" ]] && continue

  FUNCTIONS_JSON="$(gcloud functions list --v2 --regions="${REGION}" --project "${PROJECT}" --format=json)"
  COUNT="$(echo "${FUNCTIONS_JSON}" | jq 'length')"
  if [[ "${COUNT}" -eq 0 ]]; then
    continue
  fi

  # Redact all environment variable values to avoid writing sensitive data to disk.
  FUNCTIONS_JSON="$(
    echo "${FUNCTIONS_JSON}" | jq '
      map(
        .serviceConfig.environmentVariables = (
          (.serviceConfig.environmentVariables // {})
          | to_entries
          | map({key, value: "[REDACTED]"})
          | from_entries
        )
      )
    '
  )"

  FILE="${OUT}/cloud_functions_v2_${PROJECT}_${REGION}_${TS}.json"
  echo "${FUNCTIONS_JSON}" | jq '.' >"${FILE}"
  echo "Wrote ${FILE}"
done

SUMMARY="${OUT}/cloud_functions_v2_${PROJECT}_summary_${TS}.md"
{
  echo "# Cloud Functions v2 inventory (${PROJECT})"
  echo
  echo "- Timestamp (UTC): ${TS}"
  echo
  echo "## Functions"
  echo
  echo "| Region | Function | State | URL | Runtime | Deployer |"
  echo "|---|---|---|---|---|---|"
  for f in "${OUT}"/cloud_functions_v2_"${PROJECT}"_*_"${TS}".json; do
    [[ ! -f "${f}" ]] && continue
    REGION="$(basename "${f}" | awk -F_ '{print $5}')"
    jq -r --arg region "${REGION}" '
      .[]
      | [
          $region,
          (.name | split("/") | last),
          (.state // "-"),
          (.url // "-"),
          (.buildConfig.runtime // "-"),
          (.labels["deployment-tool"] // "-")
        ]
      | @tsv
    ' "${f}" | while IFS=$'\t' read -r region fn state url runtime deployer; do
      printf "| %s | %s | %s | %s | %s | %s |\n" "${region}" "${fn}" "${state}" "${url}" "${runtime}" "${deployer}"
    done
  done
} >"${SUMMARY}"
echo "Wrote ${SUMMARY}"
