from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Vertice Agent Gateway", version="2026.1.0")


class PromptRequest(BaseModel):
    prompt: str
    session_id: str


@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "agent-gateway", "runtime": "cloud-run"}


@app.post("/agui/chat")
async def chat(request: PromptRequest):
    """
    Placeholder for the AG-UI Streaming Endpoint.
    Tomorrow we will connect this to 'vertice_core.agents'.
    """
    return {
        "thought": "Architecture Initialized. Waiting for core logic transplant.",
        "response": f"Echo: {request.prompt}",
    }
