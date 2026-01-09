
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug")

print("PYTHONPATH:", os.environ.get("PYTHONPATH"))
print("CWD:", os.getcwd())

try:
    print("Attempting to import vertice_core.clients...")
    from vertice_core.clients import get_client
    print("Import successful!")
    
    print("Attempting to get client...")
    client = get_client()
    print(f"Client created: {client}")
    
    print("Checking available providers...")
    providers = client.get_available_providers()
    print(f"Available providers: {providers}")
    
    print("Current provider:", client.current_provider)

except Exception as e:
    print(f"CRITICAL ERROR during VerticeClient init: {e}")
    import traceback
    traceback.print_exc()

print("-" * 50)
print("Testing Anthropic Import directly...")
try:
    import anthropic
    print("anthropic package found.")
    from anthropic import AnthropicVertex
    print("AnthropicVertex class found.")
except ImportError as e:
    print(f"Anthropic import failed: {e}")

print("-" * 50)
print("Testing Register.py...")
try:
    from vertice_cli.core.providers.register import ensure_providers_registered, registry
    ensure_providers_registered()
    print("Registration run.")
    print("Registry factories:", registry._factories.keys())
except Exception as e:
    print(f"Register.py failed: {e}")
    import traceback
    traceback.print_exc()
