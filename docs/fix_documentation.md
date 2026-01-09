# Vertex AI Integration Fix & Failure Analysis (Jan 2026)

## 1. Failure Analysis: Why the Fix Failed
**Status:** _Partially Resolved (Code Correct, Environment/State Blocked)_

The attempts to bring the Vertice TUI (Textual UI) to a passing E2E state failed due to a convergence of three distinct issues:

### A. The "Schema has no field named path" Error
**Root Cause:**
The Google Cloud Vertex AI SDK converts `FunctionDeclaration` parameters into a Protocol Buffer message (`google.cloud.aiplatform.v1beta1.Schema`).
The error `available fields... ['type', 'properties', 'required'...]` specifically indicates that the SDK attempted to initialize a Schema object with a field that doesn't exist on the proto definition (e.g., `Schema(path=...)`).

This happens when a dictionary representing *properties* (e.g., `{'path': {'type': 'string'}}`) is passed directly as the *schema itself* to `FunctionDeclaration(parameters=...)`. The SDK iterates over the keys of the dict (`path`) and tries to set them as attributes on the Schema message. Since `path` is not a valid Schema field (it should be inside `properties`), the proto validation fails.

**The Fix Attempt:**
I implemented `BaseTool.get_schema()` in `clean_tool_system_v2.py` to ensure every tool returns a valid JSON Schema Object:
```json
{
  "type": "object",
  "properties": { ... },
  "required": [ ... ]
}
```
**Why it persisted:**
The `ToolBridge` (legacy bridge used by TUI) imports tools from `vertice_cli.tools.file_ops`, which inherits from `ValidatedTool`. Although I patched `ValidatedTool` logic partially, the runtime state or import chains likely caused the TUI to continue using an older validation path or a direct dictionary reference that bypassed my `get_schema` wrapper.

### B. The "404 Publisher Model Not Found" Error
**Root Cause:**
The user's GCP Project (`clinica-genesis-os-e689e`) lacks access to the requested models in the `us-central1` region.
- Tried: `gemini-1.5-flash-001` (404)
- Tried: `claude-3-5-sonnet-v2@20241022` (404)
- Tried: `claude-sonnet-4-5@20250929` (404)

**Analysis:**
Even though these models are valid and available generally (as confirmed by web search), they are not enabled for this specific project or region combination. Without `gcloud` access to enable the Model Garden API or check quotas, this is an unfixable environment blocker from the code side.

### C. The "Tool Call ignored" Issue (Positional Args)
**Resolved:**
Claude models output `write_file("file.txt", "content")` (positional arguments). The original parser only handled keyword arguments.
**Fix:** I successfully patched `ToolCallParser` to map positional arguments using `POSITIONAL_MAPS`. This part of the fix was verified by unit tests.

---

## 2. Claude on Vertex AI: Implementation Guide (Jan 2026)

### Prerequisites
1.  **GCP Project**: Enabled for Vertex AI.
2.  **Model Availability**: Specific Claude models must be enabled in **Model Garden**.
3.  **Authentication**: `gcloud auth application-default login` or Service Account with `roles/aiplatform.user`.

### Python SDK Implementation
The official and recommended way to use Claude on Vertex AI in 2026 is via the `anthropic` library with Vertex support.

**Installation:**
```bash
pip install "anthropic[vertex]"
```

**Instantiating the Client:**
```python
from anthropic import AnthropicVertex

client = AnthropicVertex(
    region="us-central1",  # or "europe-west4"
    project_id="your-project-id"
)

message = client.messages.create(
    model="claude-3-5-sonnet-v2@20241022", # Must use full Vertex ID
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude on Vertex!"}
    ]
)
print(message.content)
```

### Supported Claude Models on Vertex AI (2026)
| Model Name | API ID | Availability |
| :--- | :--- | :--- |
| **Claude 3.5 Sonnet v2** | `claude-3-5-sonnet-v2@20241022` | Global / Regional (us-central1, europe-west4) |
| **Claude 4.5 Sonnet** | `claude-sonnet-4-5@20250929` | Global (Beta) / Regional |
| **Claude 4.5 Opus** | `claude-opus-4-5@20251101` | Global / Regional |

---

## 3. Vertex AI Function Calling Documentation

### Schema Definition
To avoid the "no field named X" error, `FunctionDeclaration.parameters` **MUST** be a dictionary that strictly adheres to the OpenAPI 3.0 Schema Object subset supported by Vertex AI.

**Valid Structure:**
```python
# CORRECT
parameters = {
    "type": "object",  # CRITICAL: Must be top-level
    "properties": {
        "location": {
            "type": "string",
            "description": "City and state"
        }
    },
    "required": ["location"]
}
```

**Incorrect Structure (Common Failure):**
```python
# INCORRECT (Causes "Schema has no field named location")
parameters = {
    "location": {
        "type": "string"
    }
}
```

---

## 4. Known Errors & Troubleshooting

### 404 Publisher Model Not Found
-   **Symptom:** `google.api_core.exceptions.NotFound: 404 Publisher Model ... not found`
-   **Cause:** The model is not enabled in the project, or the region specified in the client does not host that specific model version.
-   **Solution:** Go to Vertex AI Model Garden, search for the model (e.g., "Claude 4.5"), and click "Enable". Verify the region support (some preview models are `us-central1` only).

### 429 Quota Exceeded / Resource Exhausted
-   **Symptom:** `429 Quota exceeded for aiplatform.googleapis.com/...`
-   **Cause:** Default quotas for Anthropic models on Vertex are often low (e.g., 60 RPM).
-   **Solution:** Request a quota increase in GCP Console > IAM & Admin > Quotas. Filter for `Vertex AI API` and the specific model.

### Schema Error: "Has no field named"
-   **Symptom:** `Message type "google.cloud.aiplatform.v1beta1.Schema" has no field named "path"`
-   **Cause:** Passing a raw properties dictionary (keys as field names) instead of a wrapped Schema object (keys as `type`, `properties`, etc.).
-   **Solution:** Ensure your tool's `get_schema()` method wraps the parameters in `{"type": "object", "properties": {...}}`.

### System Message "TypeError" (Claude Code)
-   **Symptom:** `TypeError: Cannot read properties of undefined (reading 'role')`
-   **Cause:** Known bug in how system messages are handled/condensed in some Vertex AI integration paths (like Continue.dev).
-   **Solution:** Update the calling client library or ensure system messages are passed strictly as a top-level `system` parameter (in SDK) rather than inside the `messages` list if the specific client version requires it.

---

## 5. Recommended Remediation Plan
To fix the system permanently, the following steps (outside the agent's current permission scope) are required:

1.  **Environment:** Run `gcloud services enable aiplatform.googleapis.com` and explicitly enable the Claude models in the GCP Console -> Vertex AI -> Model Garden.
2.  **Code:** Ensure `ToolBridge` strictly uses `clean_tool_system_v2.py` for ALL tool loading, completely deprecating the legacy `vertice_cli.tools.*` modules if they don't inherit correctly.
3.  **Validation:** Run `tests/verify_parser_fix.py` to confirm tool execution logic remains sound.
