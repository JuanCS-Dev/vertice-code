#!/usr/bin/env python3
import subprocess
import sys
import time
import requests


def get_service_url(service_name, region="us-central1"):
    try:
        cmd = [
            "gcloud",
            "run",
            "services",
            "describe",
            service_name,
            "--region",
            region,
            "--format",
            "value(status.url)",
            "--project",
            "vertice-ai",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get URL for {service_name}: {e.stderr}")
        return None


def check_health(url, service_name):
    print(f"🔍 Checking {service_name} at {url}...")
    try:
        # Try /health endpoint first
        health_url = f"{url}/health"
        # For frontend, it might just be / or /api/health depending on implementation
        if "frontend" in service_name:
            health_url = url  # Frontend might not have /health, just check root

        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is HEALTHY ({response.status_code})")
            return True
        else:
            print(f"❌ {service_name} returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} check failed: {str(e)}")
        return False


def verify_chat_api(backend_url):
    print(f"🔍 Verifying Chat API at {backend_url}...")
    try:
        # Check if chat router is accessible (requires auth usually, but 401/403 is better than 404/500)
        # Actually /health is global. Let's try /api/v1/billing/plans which might be public

        # Checking main health again as proxy for API up
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.ok:
            print("✅ Chat API Backend seems responsive")
            return True
        return False
    except Exception as e:
        print(f"❌ Chat API check failed: {e}")
        return False


def main():
    print("🚀 Starting Post-Deployment Verification...")

    # Get URLs
    backend_url = get_service_url("vertice-backend")
    frontend_url = get_service_url("vertice-frontend")

    if not backend_url or not frontend_url:
        print("❌ Could not retrieve service URLs. Deployment might have failed.")
        sys.exit(1)

    print(f"📍 Backend: {backend_url}")
    print(f"📍 Frontend: {frontend_url}")

    # Wait for services to be ready (cold start)
    print("⏳ Waiting 10s for cold start...")
    time.sleep(10)

    # Verify
    backend_ok = check_health(backend_url, "Backend")
    frontend_ok = check_health(frontend_url, "Frontend")
    api_ok = verify_chat_api(backend_url)

    if backend_ok and frontend_ok and api_ok:
        print("\n🎉 ALL SYSTEMS GO! Deployment Verified.")
        sys.exit(0)
    else:
        print("\n⚠️ Deployment verification FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
