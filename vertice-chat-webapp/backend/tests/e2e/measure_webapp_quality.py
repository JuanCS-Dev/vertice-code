import asyncio
import argparse
import sys
import os
import re
import ast
from typing import List
from unittest.mock import MagicMock, patch

# Add backend root to path to verify imports if needed for mock mode
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Force Development Environment for Auth Bypass
os.environ["ENVIRONMENT"] = "development"


class ScriptedGenerativeModel:
    """Mock Vertex AI GenerativeModel that follows a script."""

    def __init__(self, script: List[str]):
        self.script = script
        self.model_name = "mock-model"

    def start_chat(self, history=None):
        return ScriptedChatSession(self.script)


class ScriptedChatSession:
    def __init__(self, script: List[str]):
        self.script = script
        self.script_index = 0

    async def send_message_async(self, message: str, stream: bool = True):
        # Vertex AI send_message_async returns an awaitable that resolves to the stream
        # So we return the generator object directly, but since this is async def,
        # awaiting it returns the return value.
        return self._response_stream()

    async def _response_stream(self):
        response_text = self.script[0] if self.script else "Mock response"

        # Simulate Vertex AI Chunk
        chunk_size = 10
        for i in range(0, len(response_text), chunk_size):
            chunk = MagicMock()
            chunk.text = response_text[i : i + chunk_size]
            yield chunk
            await asyncio.sleep(0.01)


async def run_quality_test():
    parser = argparse.ArgumentParser(description="Web App Backend Quality Test")
    parser.add_argument("--real", action="store_true", help="Use real Backend via HTTP")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL for real mode")
    args = parser.parse_args()

    print("🚀 Starting Web App Quality Test...")
    print(f"   Mode: {'REAL HTTP' if args.real else 'MOCKED TestClient'}")

    # SCENARIO: Refactor Code
    messy_code = "def add(a,b): return a+b"
    prompt = f"Refactor this Python code into a class: {messy_code}. Output ONLY code."

    mock_response = """
Here is the refactored code:
```python
class Calculator:
    def add(self, a, b):
        return a + b
```
"""

    if args.real:
        import httpx

        url = f"{args.url}/api/v1/chat"
        headers = {"Authorization": "Bearer dev-token", "Content-Type": "application/json"}

        print(f"   Target: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"   Sending request: '{prompt[:40]}...'")
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": True,
                        "model": "gemini-3-pro-preview",
                    },
                )

                if response.status_code != 200:
                    print(f"❌ API Error: {response.status_code} - {response.text}")
                    return

                raw_content = response.text

        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return

    else:
        # MOCKED MODE
        from fastapi.testclient import TestClient

        # Patch Vertex AI
        # Patch Vertex AI AND Database
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel",
            return_value=ScriptedGenerativeModel([mock_response]),
        ), patch("app.core.database.get_db_session") as mock_get_db:  # Patch the source
            # Setup Mock DB Session
            from unittest.mock import AsyncMock

            mock_db_session = MagicMock()
            mock_db_session.add = MagicMock()
            mock_db_session.commit = AsyncMock()
            mock_db_session.flush = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            # Import App inside patch context to avoid early init issues if any
            from app.main import app

            client = TestClient(app)
            print("   Sending request via TestClient...")

            # TestClient is synchronous, but app is async.
            # StreamingResponse works with TestClient.
            # However, TestClient.post returns the response object.

            response = client.post(
                "/api/v1/chat",
                headers={
                    "Authorization": "Bearer dev-token",
                    "X-Session-ID": "11111111-1111-1111-1111-111111111111",
                },
                json={"messages": [{"role": "user", "content": prompt}], "stream": True},
            )

            if response.status_code != 200:
                print(f"❌ App Error: {response.status_code} - {response.text}")
                return

            raw_content = response.text

    # PARSE STREAM (Vercel AI SDK Protocol)
    # Format: 0:"text_chunk"\n

    print("   Parsing stream...")
    full_text = ""
    lines = raw_content.strip().split("\n")
    for line in lines:
        if line.startswith("0:"):
            # Simple parsing: remove 0: and quotes
            # Regex is safer: 0:"(.*)"
            m = re.match(r'^0:"(.*)"$', line)
            if m:
                # Unescape newlines
                chunk = m.group(1).replace("\\n", "\n").replace('\\"', '"')
                full_text += chunk

    print(f"   Received Response ({len(full_text)} chars).")

    # QUALITY ANALYSIS
    print("\n3. Assessing Result Quality...")

    # Extract Code Block
    code_match = re.search(r"```python\n(.*?)```", full_text, re.DOTALL)
    if code_match:
        code = code_match.group(1)
        print("   ✅ Code Block Found.")

        # Syntax Check
        try:
            ast.parse(code)
            print("   ✅ Syntax Check Passed.")
        except SyntaxError:
            print("   ❌ Syntax Check Failed.")

        # Semantic Check
        if "class" in code:
            print("   ✅ Semantic Check Passed (Class found).")
        else:
            print("   ❌ Semantic Check Failed (No class).")

    else:
        print("   ⚠️ No code block found. Checking raw text...")
        if "class" in full_text:
            print("   ✅ Semantic Check Passed (Class found in text).")
        else:
            print("   ❌ Semantic Check Failed.")


if __name__ == "__main__":
    asyncio.run(run_quality_test())
