export const metadata = {
  title: "Python SDK | Vertice Docs",
  description: "Complete Python SDK reference for Vertice MCP",
};

export default function PythonSDKPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-display font-bold text-text-main">
          Python SDK Reference
        </h1>
        <p className="text-text-muted">
          Complete API reference for the Vertice MCP Python SDK.
        </p>
      </div>

      {/* MCPClient */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          MCPClient
        </h2>
        <p className="text-text-muted">
          Synchronous client for interacting with the Vertice MCP.
        </p>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`class MCPClient:
    """Synchronous MCP client."""

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://mcp.vertice.ai",
        project_id: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        """
        Initialize MCP client.

        Args:
            api_key: Your Vertice API key
            endpoint: MCP server endpoint
            project_id: Google Cloud project ID
            timeout: Request timeout in seconds
        """
        ...

    def submit_task(
        self,
        prompt: str,
        agent: str = "coder",
        tools: list[str] | None = None,
        context: dict | None = None,
    ) -> AgentResponse:
        """
        Submit a task to an agent.

        Args:
            prompt: The task description
            agent: Agent type (coder, analyst, etc.)
            tools: Optional list of tools to use
            context: Additional context dict

        Returns:
            AgentResponse with result and metadata
        """
        ...

    def get_skills(self) -> list[Skill]:
        """Get available skills from the collective."""
        ...

    def get_status(self) -> ServerStatus:
        """Get MCP server status."""
        ...`}
            </code>
          </pre>
        </div>
      </section>

      {/* AsyncMCPClient */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          AsyncMCPClient
        </h2>
        <p className="text-text-muted">
          Asynchronous client with streaming support.
        </p>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`class AsyncMCPClient:
    """Asynchronous MCP client with streaming support."""

    async def submit_task(
        self,
        prompt: str,
        agent: str = "coder",
        tools: list[str] | None = None,
        context: dict | None = None,
    ) -> AgentResponse:
        """Submit a task asynchronously."""
        ...

    async def stream_task(
        self,
        prompt: str,
        agent: str = "coder",
        tools: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream task responses.

        Yields:
            StreamChunk with text, tool calls, or errors
        """
        ...

    async def get_skills(self) -> list[Skill]:
        """Get available skills asynchronously."""
        ...`}
            </code>
          </pre>
        </div>
      </section>

      {/* Types */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Types
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`@dataclass
class AgentResponse:
    """Response from an agent task."""
    task_id: str
    result: str
    status: str  # "completed", "failed", "pending"
    tool_results: list[ToolResult]
    tokens_used: int
    latency_ms: float

@dataclass
class Skill:
    """A skill available in the collective."""
    name: str
    description: str
    agent: str
    tools: list[str]
    category: str

@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    text: str
    is_final: bool
    tool_call: ToolCall | None
    error: str | None`}
            </code>
          </pre>
        </div>
      </section>

      {/* Error Handling */}
      <section className="space-y-4">
        <h2 className="text-xl font-display font-semibold text-text-main">
          Error Handling
        </h2>
        <div className="bg-obsidian-deep border border-border-dim rounded-lg overflow-hidden">
          <pre className="p-4 text-sm overflow-x-auto">
            <code className="text-text-main font-mono">
{`from vertice_mcp import MCPClient, MCPError, RateLimitError

client = MCPClient(api_key="...")

try:
    response = client.submit_task(prompt="...")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except MCPError as e:
    print(f"MCP error: {e.message}")`}
            </code>
          </pre>
        </div>
      </section>
    </div>
  );
}
