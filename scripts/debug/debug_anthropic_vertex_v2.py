import os
import asyncio
import logging
from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_anthropic")

async def test_anthropic_model(model_name_or_alias, location="us-central1"):
    print(f"\n--- Testing Model: {model_name_or_alias} in {location} ---")
    try:
        # Force location via env
        os.environ["ANTHROPIC_VERTEX_LOCATION"] = location
        
        # We instantiate directly to control the exact model name passed to SDK
        # The Provider class might map aliases, so we will bypass the mapping for raw strings if needed
        # But for now let's use the Provider but override the internal model mapping if it's not in the dict
        
        provider = AnthropicVertexProvider(
            location=location,
            model_name=model_name_or_alias,
            enable_caching=False 
        )
        
        # Hack: If the provider mapped it to something we don't want (like the old version), override it back
        # But actually we want to test exactly what we pass.
        # The provider maps "sonnet-4.5" -> "claude-sonnet-4-5@20250929".
        # We also want to test raw "claude-sonnet-4-5".
        
        # Let's manually set the model_name on the instance to be sure
        provider.model_name = model_name_or_alias
        
        print(f"Requesting Model ID: {provider.model_name}")
        
        messages = [{"role": "user", "content": "Hello. Reply 'YES'."}]
        
        # Test generate
        print("Sending request...")
        response = await provider.generate(messages, max_tokens=10)
        print(f"Response: {response}")
        return True
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

async def main():
    print("Starting Anthropic Vertex Diagnostic (Deep Probe)...")
    
    current_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    print(f"DEBUG: Current GCP Project: {current_project}")
    
    # Models to test
    models_to_test = [
        # User suggestions
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        # Full versions
        "claude-opus-4-5@20251101",
        "claude-sonnet-4-5@20250929",
    ]
    
    locations_to_try = [
        "us-east5",      # Columbus (Primary for Anthropic)
        "europe-west1",  # Belgium (Secondary)
        "us-central1",   # Iowa (Google Main)
        "us-west1",      # Oregon
    ]
    
    success_found = False
    
    for model in models_to_test:
        for loc in locations_to_try:
            if await test_anthropic_model(model, location=loc):
                print(f"🌟🌟🌟 MATCH FOUND: {model} in {loc} 🌟🌟🌟")
                success_found = True
                break # Move to next model
        if success_found:
            # If we found a working configuration for one model, keep checking others? 
            # Yes, we want to know if both work.
            pass

if __name__ == "__main__":
    asyncio.run(main())