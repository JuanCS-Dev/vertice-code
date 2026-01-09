
import os
import asyncio
import logging
from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_anthropic")

async def main():
    print("Starting Anthropic Vertex Diagnostic (FINAL CHECK)...")
    
    # FORCE THE CORRECT PROJECT
    target_project = "vertice-ai"
    os.environ["GOOGLE_CLOUD_PROJECT"] = target_project
    print(f"DEBUG: Enforced GCP Project: {target_project}")
    
    # Models to test (EXACTLY as user specified, no dates)
    models_to_test = [
        "claude-opus-4-5",
        "claude-sonnet-4-5"
    ]
    
    locations_to_try = [
        "us-east5",      
        "europe-west1",
        "us-central1"
    ]
    
    for model in models_to_test:
        print(f"\n>>> Testing {model} <<<")
        success = False
        for loc in locations_to_try:
            print(f"  --- Location: {loc} ---")
            try:
                # Force location
                os.environ["ANTHROPIC_VERTEX_LOCATION"] = loc
                
                provider = AnthropicVertexProvider(
                    project=target_project, # Pass explicitly
                    location=loc,
                    model_name=model,
                    enable_caching=False 
                )
                
                # FORCE OVERRIDE ANY MAPPING
                provider.model_name = model 
                
                print(f"  Requesting Model ID: {provider.model_name}")
                
                messages = [{"role": "user", "content": "Hello."}]
                
                response = await provider.generate(messages, max_tokens=10)
                print(f"  ✅ SUCCESS! Response: {response}")
                success = True
                break
            except Exception as e:
                print(f"  ❌ FAILED: {e}")
        
        if success:
            print(f"🌟 {model} is AVAILABLE!")
        else:
            print(f"❌ {model} is NOT available in any tested region.")

if __name__ == "__main__":
    asyncio.run(main())
