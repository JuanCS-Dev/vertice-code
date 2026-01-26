#!/usr/bin/env python3
import os
import subprocess
import sys
import re
import time
from typing import Dict, Optional

# --- Configuration ---
PROJECT_ID_CMD = "gcloud config get-value project"
REGION = "us-central1"
BACKEND_SERVICE = "vertice-agent-gateway"
ENV_FILE = "vertice-chat-webapp/frontend/.env.local"
CLOUDBUILD_FILE = "cloudbuild.yaml"


def run_command(cmd: str, check: bool = True) -> Optional[str]:
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {cmd}\nStderr: {e.stderr}")
            sys.exit(1)
        return None


def get_firebase_config_from_env_file() -> Optional[Dict[str, str]]:
    """Parse .env.local for Firebase config."""
    if not os.path.exists(ENV_FILE):
        return None

    print(f"Reading configuration from {ENV_FILE}...")
    config = {}
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                # Strip quotes
                value = value.strip(' "')
                config[key] = value

    # Map to cloudbuild substitutions
    mapping = {
        "NEXT_PUBLIC_FIREBASE_API_KEY": "_FIREBASE_API_KEY",  # pragma: allowlist secret
        "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN": "_FIREBASE_AUTH_DOMAIN",
        "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "_FIREBASE_PROJECT_ID",
        "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET": "_FIREBASE_STORAGE_BUCKET",
        "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID": "_FIREBASE_MESSAGING_SENDER_ID",
        "NEXT_PUBLIC_FIREBASE_APP_ID": "_FIREBASE_APP_ID"
    }

    final_config = {}
    for env_key, sub_key in mapping.items():
        if env_key in config:
            final_config[sub_key] = config[env_key]
        else:
            print(f"Warning: {env_key} missing in {ENV_FILE}")
            return None  # Partial config is useless

    return final_config


def get_firebase_config_from_cli(project_id: str) -> Optional[Dict[str, str]]:
    """Fetch Firebase config via CLI."""
    print("Fetching configuration via Firebase CLI...")
    output = run_command(f"firebase apps:sdkconfig web --project {project_id}", check=False)
    if not output:
        return None

    # Regex extraction for robustness against multiline format
    def extract(key_pattern: str) -> str:
        match = re.search(f'"{key_pattern}": "(.*?)"', output)
        return match.group(1) if match else ""

    config = {
        "_FIREBASE_API_KEY": extract("apiKey"),
        "_FIREBASE_AUTH_DOMAIN": extract("authDomain"),
        "_FIREBASE_PROJECT_ID": extract("projectId"),
        "_FIREBASE_STORAGE_BUCKET": extract("storageBucket"),
        "_FIREBASE_MESSAGING_SENDER_ID": extract("messagingSenderId"),
        "_FIREBASE_APP_ID": extract("appId"),
    }

    if not config["_FIREBASE_API_KEY"]:
        return None

    return config


def main():
    print("--- M5 Cutover: Robust Deployment Script (Python) ---")

    # 1. Project ID
    project_id = run_command(PROJECT_ID_CMD)
    print(f"Project ID: {project_id}")

    # 2. Backend URL
    print("Fetching Backend URL...")
    backend_url = run_command(
        f"gcloud run services describe {BACKEND_SERVICE} --region {REGION} --format='value(status.url)'",
        check=False,
    )
    if not backend_url:
        backend_url = f"https://{BACKEND_SERVICE}-{project_id}.a.run.app"
        print(f"Warning: Backend service not found. Using placeholder: {backend_url}")
    else:
        print(f"Backend URL: {backend_url}")

    # 3. Firebase Config
    config = get_firebase_config_from_env_file()
    if not config:
        config = get_firebase_config_from_cli(project_id)

    if not config:
        print("CRITICAL ERROR: Could not determine Firebase Configuration.")
        print(
            "Ensure vertice-chat-webapp/frontend/.env.local exists OR 'firebase login' is active."
        )
        sys.exit(1)

    # 4.5 Get Commit SHA
    print("Fetching Git Commit SHA...")
    commit_sha = run_command("git rev-parse HEAD", check=False)
    if not commit_sha:
        print("Warning: Could not fetch git commit SHA. Using 'manual-build'.")
        commit_sha = "manual-build"
    print(f"Commit SHA: {commit_sha}")

    # 5. Construct Substitutions
    substitutions = [f"_REGION={REGION}", f"_API_URL={backend_url}", f"COMMIT_SHA={commit_sha}"]
    for key, value in config.items():
        substitutions.append(f"{key}={value}")

    subs_str = ",".join(substitutions)

    # 6. Submit Build
    print("\nSubmitting Cloud Build (Async)...")
    build_cmd = f"gcloud builds submit --config {CLOUDBUILD_FILE} --async --format='value(id)' --substitutions={subs_str} ."

    build_id = run_command(build_cmd)

    if build_id:
        print(f"Build submitted successfully! ID: {build_id}")
        print(f"To stream logs, run: gcloud builds log --stream {build_id}")

        # Optional: Auto-stream
        print("\nStreaming logs in 3 seconds (Ctrl+C to stop streaming, build will continue)...")
        time.sleep(3)
        os.system(f"gcloud builds log --stream {build_id}")
    else:
        print("Error: Build submission failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
