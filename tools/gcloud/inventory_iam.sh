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

POLICY_FILE="${OUT}/iam_policy_${PROJECT}_${TS}.json"
gcloud projects get-iam-policy "${PROJECT}" --format=json | jq '.' >"${POLICY_FILE}"
echo "Wrote ${POLICY_FILE}"

SAS_FILE="${OUT}/service_accounts_${PROJECT}_${TS}.json"
gcloud iam service-accounts list --project "${PROJECT}" --format=json | jq '.' >"${SAS_FILE}"
echo "Wrote ${SAS_FILE}"

SUMMARY="${OUT}/iam_${PROJECT}_summary_${TS}.md"
{
  echo "# IAM inventory (${PROJECT})"
  echo
  echo "- Timestamp (UTC): ${TS}"
  echo
  echo "## Service Accounts"
  echo
  echo "| Email | Disabled |"
  echo "|---|---|"
  jq -r '.[] | [(.email // "-"), (.disabled // false)] | @tsv' "${SAS_FILE}" \
    | while IFS=$'\t' read -r email disabled; do
      printf "| %s | %s |\n" "${email}" "${disabled}"
    done
  echo
  echo "## Basic roles (owner/editor/viewer)"
  echo
  echo "| Role | Member |"
  echo "|---|---|"
  jq -r '
    (.bindings // [])
    | map(select(.role=="roles/owner" or .role=="roles/editor" or .role=="roles/viewer"))
    | .[]
    | .role as $role
    | (.members // [])[]
    | [$role, .]
    | @tsv
  ' "${POLICY_FILE}" | while IFS=$'\t' read -r role member; do
    printf "| %s | %s |\n" "${role}" "${member}"
  done
} >"${SUMMARY}"
echo "Wrote ${SUMMARY}"
