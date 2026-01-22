import asyncio
import os
from google import genai
from google.genai import types

async def probe_streaming_behavior():
    print("\n📡 **Live Streaming Probe (Model Discovery)**")
    print("-" * 40)
    
    project = "vertice-ai" 
    locations = ["us-central1"] # Focus on standard region first
    
    for loc in locations:
        print(f"\n🌍 Testing Location: {loc}")
        try:
            client = genai.Client(vertexai=True, project=project, location=loc)
            
            # List Models Correctly
            print(f"   📋 Listing Models in {loc}...")
            try:
                # Based on SDK patterns, list() usually returns a Pager or List
                # We await the call first
                response = await client.aio.models.list(config={'page_size': 10})
                
                # Check if response is iterable directly or has .models
                models = response.models if hasattr(response, 'models') else response
                
                count = 0
                for m in models:
                    print(f"      FOUND: {m.name} (ID: {m.name.split('/')[-1] if hasattr(m, 'name') else '?'})")
                    count += 1
                
                if count == 0:
                    print("      ⚠️ No models found (Empty List).")
                    
            except Exception as e:
                print(f"      ⚠️ List Models Failed: {e}")

        except Exception as e:
            print(f"   🔥 Client Init Failed for {loc}: {e}")

if __name__ == "__main__":
    asyncio.run(probe_streaming_behavior())
