#!/usr/bin/env python3
import requests
import sys
import time

FRONTEND_URL = "https://vertice-frontend-nrpngfmr6a-uc.a.run.app"
BACKEND_URL = "https://vertice-backend-nrpngfmr6a-uc.a.run.app"

def check_url(url, name, expected_codes=[200]):
    print(f"🔍 Checking {name} ({url})...", end=" ")
    try:
        start = time.time()
        resp = requests.get(url, timeout=10)
        duration = (time.time() - start) * 1000
        
        if resp.status_code in expected_codes:
            print(f"✅ OK ({resp.status_code}) - {duration:.0f}ms")
            return True
        else:
            print(f"❌ FAILED ({resp.status_code})")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_asset(url, name):
    print(f"🎨 Verifying Asset {name}...", end=" ")
    try:
        resp = requests.head(url, timeout=5)
        if resp.status_code == 200:
            print("✅ FOUND")
            return True
        else:
            print(f"❌ MISSING ({resp.status_code})")
            return False
    except:
        print("❌ ERROR")
        return False

def main():
    print("="*60)
    print("👽 VERTICE LIVE SYSTEM AUDIT (2026)")
    print("="*60)
    
    success = True
    
    # 1. Backend Health
    success &= check_url(f"{BACKEND_URL}/health", "Backend Health")
    success &= check_url(f"{BACKEND_URL}/", "Backend Root")
    
    # 2. Frontend Health
    success &= check_url(f"{FRONTEND_URL}/", "Frontend App (Home)")
    success &= check_url(f"{FRONTEND_URL}/sign-in", "Frontend Sign-In")
    
    # 3. Critical Assets (Proof of Build)
    success &= check_asset(f"{FRONTEND_URL}/grid.svg", "Background Grid")
    success &= check_asset(f"{FRONTEND_URL}/favicon.ico", "Favicon")
    
    print("-" * 60)
    if success:
        print("✅ SYSTEM STATUS: OPERATIONAL")
        print("🚀 Ready for User Login.")
        sys.exit(0)
    else:
        print("❌ SYSTEM STATUS: DEGRADED")
        sys.exit(1)

if __name__ == "__main__":
    main()
