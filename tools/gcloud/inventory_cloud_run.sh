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
  # Prefer Cloud Asset Inventory to avoid iterating every Cloud Run region.
  # Falls back if Cloud Asset API isn't enabled.
  gcloud asset search-all-resources \
    --scope="projects/${PROJECT}" \
    --asset-types="run.googleapis.com/Service" \
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

  # Minimal fallback: configured Cloud Run region + common secondary region used in this repo.
  {
    gcloud config get-value run/region 2>/dev/null || true
    echo "southamerica-east1"
  } | rg -v '^(\\(unset\\)|-)$' | sort -u
}

REGIONS="$(regions_from_assets || true)"
if [[ -z "${REGIONS}" ]]; then
  REGIONS="$(regions_from_env_or_config)"
fi

echo "${REGIONS}" | while read -r REGION; do
  [[ -z "${REGION}" ]] && continue
  SERVICES_JSON="$(gcloud run services list --project "${PROJECT}" --region "${REGION}" --platform managed --format=json)"
  COUNT="$(echo "${SERVICES_JSON}" | jq 'length')"
  if [[ "${COUNT}" -eq 0 ]]; then
    continue
  fi

  # Redact any literal env var values to avoid writing sensitive data to disk.
  # Keep env var names and keep valueFrom references (secret/config provenance).
  SERVICES_JSON="$(
    echo "${SERVICES_JSON}" | jq '
      map(
        .spec.template.spec.containers |= map(
          .env = (
            (.env // [])
            | map(
                if has("valueFrom") then
                  {name, valueFrom}
                else
                  {name, valueRedacted: true}
                end
              )
          )
        )
      )
    '
  )"

  FILE="${OUT}/cloud_run_${PROJECT}_${REGION}_${TS}.json"
  echo "${SERVICES_JSON}" | jq '.' >"${FILE}"
  echo "Wrote ${FILE}"
done

SUMMARY="${OUT}/cloud_run_${PROJECT}_summary_${TS}.md"
{
  echo "# Cloud Run inventory (${PROJECT})"
  echo
  echo "- Timestamp (UTC): ${TS}"
  echo
  echo "## Services"
  echo
  echo "| Region | Service | URL | Ready | SA |"
  echo "|---|---|---|---|---|"
  for f in "${OUT}"/cloud_run_"${PROJECT}"_*_"${TS}".json; do
    [[ ! -f "${f}" ]] && continue
    REGION="$(basename "${f}" | awk -F_ '{print $4}')"
    jq -r --arg region "${REGION}" '
      .[]
      | [
          $region,
          .metadata.name,
          (.status.url // "-"),
          ((.status.conditions // []) | map(select(.type=="Ready"))[0].status // "-"),
          (.spec.template.spec.serviceAccountName // "-")
        ]
      | @tsv
    ' "${f}" | while IFS=$'\t' read -r region name url ready sa; do
      printf "| %s | %s | %s | %s | %s |\n" "${region}" "${name}" "${url}" "${ready}" "${sa}"
    done
  done
} >"${SUMMARY}"
echo "Wrote ${SUMMARY}"
