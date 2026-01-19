# PROMETHEUS Architecture Diagrams

## System Architecture

```mermaid
graph TB
    subgraph "Local Nexus 🖥️"
        CLI[vertice CLI<br/>Rust-style Python]
        TUI[Textual TUI<br/>Matrix Style]
        Gradio[Gradio Dashboard<br/>Cyberpunk UI]
    end

    subgraph "Protocol Layer 🔌"
        MCP[Model Context Protocol<br/>File/Git/Terminal Access]
    end

    subgraph "Remote Cortex (Blaxel) ☁️"
        Gemini[Gemini 3 Pro<br/>2M Context Window]
        MIRIX[(MIRIX Memory<br/>6 Types)]
        SimuRA[SimuRA World Model<br/>MCTS Simulation]
        Agent0[Agent0 Evolution<br/>Co-Evolution Loop]
    end

    CLI --> MCP
    TUI --> MCP
    Gradio --> MCP
    MCP --> Gemini
    Gemini --> MIRIX
    Gemini --> SimuRA
    Gemini --> Agent0

    MIRIX -->|Episodic| Gemini
    MIRIX -->|Procedural| Gemini
    SimuRA -->|Predicted States| Gemini
    Agent0 -->|Improved Tools| Gemini

    style Gemini fill:#4285F4,stroke:#1967D2,color:#fff
    style MIRIX fill:#34A853,stroke:#188038,color:#fff
    style SimuRA fill:#FBBC04,stroke:#F9AB00,color:#000
    style Agent0 fill:#EA4335,stroke:#C5221F,color:#fff
    style MCP fill:#9AA0A6,stroke:#5F6368,color:#fff
```

## MCP Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant TUI as Textual TUI
    participant MCP as MCP Server
    participant Blaxel as Blaxel Agent
    participant Gemini as Gemini 3 Pro
    participant Tools as Tool Registry

    User->>TUI: /plan "Deploy to production"
    TUI->>MCP: list_tools()
    MCP-->>TUI: [git, bash, file, web_search, ...]

    TUI->>Blaxel: POST /agent/execute
    Blaxel->>Gemini: stream_generate_content(prompt, tools)

    Note over Gemini: SimuRA: Simulating action
    Gemini->>Gemini: MCTS(git push --force)
    Gemini->>Gemini: Evaluate 3 futures

    Gemini-->>Blaxel: [TOOL_CALL:git:status]
    Blaxel->>MCP: call_tool("git", {"cmd": "status"})
    MCP->>Tools: execute(git_status)
    Tools-->>MCP: {"stdout": "clean"}
    MCP-->>Blaxel: tool_result

    Blaxel->>Gemini: continue_with_result()

    Note over Gemini: MIRIX: Check memory
    Gemini->>MIRIX: recall("git push errors")
    MIRIX-->>Gemini: [Episode: 2025-11-20 force push failed]

    Gemini-->>Blaxel: Stream response
    Blaxel-->>TUI: SSE chunks
    TUI->>User: Display plan with warnings
```

## Agent0 Co-Evolution Loop

```mermaid
flowchart LR
    subgraph "Agent0 Evolution Cycle"
        Curriculum[Curriculum Agent<br/>Gemini 2.0 Flash Thinking]
        Executor[Executor Agent<br/>Gemini 3 Pro]
        Reflection[Reflection Engine]

        Curriculum -->|Generate Challenge| Executor
        Executor -->|Attempt Solution| Reflection
        Reflection -->|Critique & Score| Curriculum
        Reflection -->|Update| MIRIX[(MIRIX Memory)]
        MIRIX -->|Load Context| Executor
    end

    style Curriculum fill:#4285F4,color:#fff
    style Executor fill:#34A853,color:#fff
    style Reflection fill:#EA4335,color:#fff
    style MIRIX fill:#FBBC04,color:#000
```

## MIRIX Memory System

```mermaid
graph TD
    Input[User Input / Tool Result]

    Input --> Core[Core Memory<br/>System Prompt]
    Input --> Episodic[Episodic Memory<br/>Timestamped Events]
    Input --> Semantic[Semantic Memory<br/>Extracted Knowledge]
    Input --> Procedural[Procedural Memory<br/>How-To Steps]
    Input --> Resource[Resource Memory<br/>File/Code References]
    Input --> Vault[Vault Memory<br/>Encrypted Secrets]

    Core -.->|Influences| Gemini[Gemini 3 Pro]
    Episodic -.->|Recent Context| Gemini
    Semantic -.->|Knowledge Base| Gemini
    Procedural -.->|Action Templates| Gemini
    Resource -.->|File Context| Gemini
    Vault -.->|API Keys| Gemini

    style Core fill:#4285F4,color:#fff
    style Episodic fill:#34A853,color:#fff
    style Semantic fill:#FBBC04,color:#000
    style Procedural fill:#EA4335,color:#fff
    style Resource fill:#9AA0A6,color:#fff
    style Vault fill:#5F6368,color:#fff
```

## SimuRA World Model (MCTS)

```mermaid
graph TD
    Start[Current State]
    Start --> Simulate{Simulate Action}

    Simulate -->|Future 1: Success| F1[+10 score<br/>Production deployed]
    Simulate -->|Future 2: Failure| F2[-5 score<br/>Build breaks]
    Simulate -->|Future 3: Partial| F3[+3 score<br/>Deploy succeeds but tests fail]

    F1 --> Select{Select Best Path}
    F2 --> Select
    F3 --> Select

    Select -->|Best: Future 1| Execute[Execute Action]
    Execute --> Verify[Verify Outcome]
    Verify -->|Match?| Update[Update World Model]

    style Start fill:#4285F4,color:#fff
    style Simulate fill:#FBBC04,color:#000
    style F1 fill:#34A853,color:#fff
    style F2 fill:#EA4335,color:#fff
    style F3 fill:#FF6D00,color:#fff
    style Execute fill:#1967D2,color:#fff
```

## Tool Execution Pipeline

```mermaid
flowchart LR
    Request[Tool Request]

    Request --> Validate[Schema Validation]
    Validate -->|Valid| Authorize[Authorization Check]
    Validate -->|Invalid| Reject1[Reject]

    Authorize -->|Allowed| Sandbox[Execute in Sandbox]
    Authorize -->|Denied| Reject2[Reject]

    Sandbox --> Monitor[Resource Monitor]
    Monitor -->|Timeout| Kill[Kill Process]
    Monitor -->|Success| Capture[Capture Output]

    Capture --> Parse[Parse Result]
    Parse --> Return[Return to LLM]

    style Validate fill:#4285F4,color:#fff
    style Authorize fill:#FBBC04,color:#000
    style Sandbox fill:#34A853,color:#fff
    style Monitor fill:#EA4335,color:#fff
```

---

## Diagram Usage

To embed these diagrams in the README, use:

\`\`\`markdown
![PROMETHEUS Architecture](docs/ARCHITECTURE_DIAGRAMS.md#system-architecture)
\`\`\`

Or for GitHub, the Mermaid will render automatically if included in the README directly.
