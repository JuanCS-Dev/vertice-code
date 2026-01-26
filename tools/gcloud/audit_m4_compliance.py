import subprocess
import json
from typing import Optional, List, Dict, Any


def run_command(cmd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e.stderr}")
        return None


def audit_cloud_run_secrets(region: str = "us-central1") -> None:
    print(f"--- Auditing Cloud Run Secrets in {region} ---")
    services_json = run_command(f"gcloud run services list --region {region} --format=json")
    if not services_json:
        return

    services: List[Dict[str, Any]] = json.loads(services_json)
    sensitive_keywords: List[str] = ["KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL", "AUTH"]

    for service in services:
        name: str = service.get("metadata", {}).get("name", "unknown")
        print(f"Checking service: {name}")

        containers: List[Dict[str, Any]] = (
            service.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        )
        for container in containers:
            env_vars: List[Dict[str, Any]] = container.get("env", [])
            for env in env_vars:
                key: str = env.get("name", "")

                # Check for Secret Manager reference
                if "valueFrom" in env and "secretKeyRef" in env["valueFrom"]:
                    print(f"  [OK] {key} uses Secret Manager.")
                    continue

                # Check for plain text sensitive data
                if any(k in key.upper() for k in sensitive_keywords):
                    value: str = env.get("value", "")
                    if value:
                        print(
                            f"  [WARN] {key} appears to be a sensitive value stored in PLAIN TEXT environment variable."
                        )
                    else:
                        print(f"  [INFO] {key} is defined but empty/unknown source.")


def audit_iam_policies(region: str = "us-central1") -> None:
    print(f"\n--- Auditing IAM Policies in {region} ---")
    # List of backend services that should NOT be public
    private_services: List[str] = ["vertice-agent-gateway", "vertice-backend", "vertice-mcp"]

    for service in private_services:
        print(f"Checking IAM for: {service}")
        policy_json = run_command(
            f"gcloud run services get-iam-policy {service} --region {region} --format=json"
        )
        if not policy_json:
            print(f"  [SKIP] Could not fetch policy for {service} (might not exist)")
            continue

        policy: Dict[str, Any] = json.loads(policy_json)
        bindings: List[Dict[str, Any]] = policy.get("bindings", [])

        is_public: bool = False
        for binding in bindings:
            members: List[str] = binding.get("members", [])
            role: str = binding.get("role", "")
            if "allUsers" in members and "roles/run.invoker" in role:
                is_public = True
                break

        if is_public:
            print(f"  [CRITICAL] {service} is PUBLIC accessible (allUsers has roles/run.invoker).")
        else:
            print(f"  [OK] {service} is not public.")


if __name__ == "__main__":
    audit_cloud_run_secrets()
    audit_iam_policies()
