import sys
import os
import asyncio
import logging
import traceback

# Add project root AND src to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(root_dir, 'src')

# Prioritize src to pick up the correct 'vertice_cli' package
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force Vertex AI Location
os.environ["VERTEX_AI_LOCATION"] = "us-central1"

async def diagnose():
    print("🚀 Starting Webchat Backend Diagnostic (Vertex AI Check)")
    print(f"📂 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Path [0]: {sys.path[0]}")
    print(f"🐍 Python Path [1]: {sys.path[1]}")
    
    # DEBUG IMPORT
    print("\n🔍 Debugging 'src.providers.vertice_router' import...")
    try:
        # Check which vertice_cli is being picked up
        import vertice_cli
        print(f"ℹ️  'vertice_cli' imported from: {vertice_cli.__file__}")
        
        import src.providers.vertice_router
        print("✅ Successfully imported src.providers.vertice_router directly.")
    except Exception as e:
        print(f"❌ Failed to import src.providers.vertice_router:")
        traceback.print_exc()

    
    try:
        import app
        import app.api
        from app.api.v1.chat import stream_ai_sdk_response, ChatMessage, ChatRequest
        print("\n✅ Successfully imported app.api.v1.chat")
    except ImportError as e:
        print(f"❌ Failed to import chat module: {e}")
        return

    # Create a test message
    messages = [
        ChatMessage(role="user", content="Hello, are you running on Vertex AI? Please identify your model.")
    ]
    
    print("\n📝 Streaming response...")
    response_text = ""
    try:
        async for chunk in stream_ai_sdk_response(messages):
            # chunk might be bytes or string depending on implementation
            # Protocol chunks are 0:"text"
            print(f"Chunk: {chunk!r}")
            response_text += str(chunk)
            
        print(f"\n✅ Full Response: {response_text}")
        
    except Exception as e:
        print(f"❌ Error during streaming: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose())