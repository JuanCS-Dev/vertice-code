#!/usr/bin/env python
"""
WebApp E2E Audit Script - Complete Functional Testing.

Tests all major features of the Vertice Chat WebApp:
1. Backend imports (FastAPI, core, llm)
2. Backend API endpoints
3. LLM integration (Vertex AI)
4. Stream protocol
5. Existing tests
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend to path
WEBAPP_ROOT = Path("/media/juan/DATA/Vertice-Code/vertice-chat-webapp")
BACKEND_ROOT = WEBAPP_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

# Results tracking
RESULTS: Dict[str, List[Tuple[str, bool, str]]] = {
    "imports": [],
    "api": [],
    "llm": [],
    "protocol": [],
    "tests": [],
}


def log_result(category: str, test_name: str, passed: bool, message: str = ""):
    """Log a test result."""
    status = "✅" if passed else "❌"
    print(f"  {status} {test_name}: {message}")
    RESULTS[category].append((test_name, passed, message))


def test_backend_imports():
    """Test backend imports."""
    print("\n" + "="*60)
    print("1. BACKEND IMPORTS")
    print("="*60)
    
    imports = [
        ("app.main", "FastAPI app"),
        ("app.core.config", "Configuration"),
        ("app.core.auth", "Authentication"),
        ("app.api.v1.chat", "Chat endpoint"),
        ("app.core.stream_protocol", "Stream protocol"),
    ]
    
    for module, desc in imports:
        try:
            __import__(module)
            log_result("imports", desc, True, "imported")
        except Exception as e:
            log_result("imports", desc, False, str(e)[:60])


def test_api_structure():
    """Test API structure."""
    print("\n" + "="*60)
    print("2. API STRUCTURE")
    print("="*60)
    
    try:
        from app.main import app
        log_result("api", "FastAPI app", True, "created")
        
        # List routes
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        log_result("api", "Routes loaded", True, f"{len(routes)} routes")
        
        # Check critical endpoints
        critical = ["/health", "/api/v1/chat"]
        for endpoint in critical:
            found = any(endpoint in r for r in routes)
            log_result("api", f"Endpoint: {endpoint}", found, 
                      "found" if found else "NOT found")
            
    except Exception as e:
        log_result("api", "FastAPI app", False, str(e)[:60])


def test_llm_integration():
    """Test LLM integration."""
    print("\n" + "="*60)
    print("3. LLM INTEGRATION")
    print("="*60)
    
    try:
        from app.llm.router import ModelTier, IntentType, route_to_model, Message
        log_result("llm", "LLM Router import", True, "imported")
        
        # Test ModelTier enum
        log_result("llm", "ModelTier.GEMINI_FAST", True, f"{ModelTier.GEMINI_FAST.value}")
        
        # Test route_to_model
        test_msgs = [Message(role="user", content="Hello")]
        model = route_to_model(test_msgs, "test-user")
        log_result("llm", "route_to_model", True, f"routed to {model}")
            
    except Exception as e:
        log_result("llm", "LLM Router", False, str(e)[:60])


def test_stream_protocol():
    """Test stream protocol."""
    print("\n" + "="*60)
    print("4. STREAM PROTOCOL")
    print("="*60)
    
    try:
        from app.core.stream_protocol import (
            format_text_chunk,
            format_finish,
            format_error,
        )
        log_result("protocol", "format_text_chunk", True, "imported")
        log_result("protocol", "format_finish", True, "imported")
        log_result("protocol", "format_error", True, "imported")
        
        # Test format_text_chunk
        result = format_text_chunk("Hello world")
        expected_format = result.startswith('0:"') and result.endswith('"\n')
        log_result("protocol", "format_text_chunk works", expected_format, f"output: {result[:30]}")
        
    except Exception as e:
        log_result("protocol", "Stream protocol", False, str(e)[:80])


def test_existing_tests():
    """Run pytest on existing tests."""
    print("\n" + "="*60)
    print("5. EXISTING TESTS (pytest)")
    print("="*60)
    
    import subprocess
    
    test_dirs = [
        ("unit", BACKEND_ROOT / "tests" / "unit"),
        ("integration", BACKEND_ROOT / "tests" / "integration"),
    ]
    
    for name, test_dir in test_dirs:
        if test_dir.exists():
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_dir), "-v", "--tb=no", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(BACKEND_ROOT)
                )
                
                # Parse output
                if result.returncode == 0:
                    log_result("tests", f"{name} tests", True, "all passed")
                else:
                    # Count passed/failed from output
                    output = result.stdout + result.stderr
                    if "passed" in output:
                        log_result("tests", f"{name} tests", False, output.split('\n')[-2][:60])
                    else:
                        log_result("tests", f"{name} tests", False, "failed")
                        
            except subprocess.TimeoutExpired:
                log_result("tests", f"{name} tests", False, "timeout")
            except Exception as e:
                log_result("tests", f"{name} tests", False, str(e)[:60])
        else:
            log_result("tests", f"{name} tests", False, "dir not found")


def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for category, results in RESULTS.items():
        passed = sum(1 for _, p, _ in results if p)
        failed = sum(1 for _, p, _ in results if not p)
        total_passed += passed
        total_failed += failed
        
        status = "✅" if failed == 0 else "❌"
        print(f"{status} {category.upper()}: {passed}/{passed+failed} passed")
    
    print("-" * 40)
    total = total_passed + total_failed
    print(f"TOTAL: {total_passed}/{total} passed ({int(total_passed/total*100) if total > 0 else 0}%)")
    
    if total_failed > 0:
        print("\n❌ FAILED TESTS:")
        for category, results in RESULTS.items():
            for name, passed, msg in results:
                if not passed:
                    print(f"  - {category}/{name}: {msg}")
    
    return total_failed == 0


def main():
    """Run all tests."""
    print("="*60)
    print("VERTICE WEBAPP E2E AUDIT")
    print("="*60)
    
    os.chdir(BACKEND_ROOT)
    
    test_backend_imports()
    test_api_structure()
    test_llm_integration()
    test_stream_protocol()
    test_existing_tests()
    
    success = print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
