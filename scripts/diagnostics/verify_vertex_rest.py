
import subprocess
import requests
import json
import sys

def get_access_token():
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get access token: {e}")
        sys.exit(1)

def test_rest_api():
    project_id = "vertice-ai"
    location = "us-central1"
    # JAN 2026 STANDARD: Gemini 2.5 Pro
    model_id = "gemini-2.5-pro"
    
    print(f"🔍 RAW REST API DIAGNOSTIC (2026): {project_id} @ {location}")
    print(f"   🎯 TARGET MODEL: {model_id}")
    
    token = get_access_token()
    print("   🔑 Access Token acquired.")
    
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": {
            "role": "USER",
            "parts": {"text": "Hello from RAW REST API!"}
        }
    }
    
    print(f"   📡 POST {url}...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"   Response Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! API is reachable and working.")
            print("-" * 40)
            print(json.dumps(response.json(), indent=2))
            print("-" * 40)
        else:
            print("   ❌ FAILURE.")
            print("-" * 40)
            print(response.text)
            print("-" * 40)
            
            if response.status_code == 404:
                print("   🚨 404 CONFIRMED: The endpoint URL or Model ID is invalid for this project/region.")
            elif response.status_code == 403:
                 print("   🚨 403 PERMISSION DENIED: Token lacks scope or IAM role.")
    
    except Exception as e:
        print(f"   ❌ Network Error: {e}")

if __name__ == "__main__":
    test_rest_api()
