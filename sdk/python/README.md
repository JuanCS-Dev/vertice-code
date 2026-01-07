# Vertice MCP Python SDK

[![PyPI version](https://badge.fury.io/py/vertice-mcp.svg)](https://pypi.org/project/vertice-mcp/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Python SDK for Vertice Model Context Protocol - Collective AI Ecosystem**

This SDK provides a complete Python interface to the Vertice MCP (Model Context Protocol) server, enabling seamless integration with the collective AI ecosystem.

## 🚀 Features

- **Asynchronous & Synchronous APIs** - Choose the best approach for your application
- **Type-Safe Operations** - Full type hints and validation
- **Intelligent Error Handling** - Comprehensive error types and recovery
- **Skill Management** - Learn, share, and retrieve skills from the collective
- **Task Orchestration** - Submit and monitor tasks across the AI collective
- **Real-time Status** - Monitor system health and performance

## 📦 Installation

```bash
pip install vertice-mcp
```

## 🏁 Quick Start

```python
from vertice_mcp import MCPClient, AgentTask, Skill

# Initialize client
client = MCPClient()

# Submit a task
task = AgentTask(
    id="my-task-1",
    description="Analyze this dataset and provide insights",
    agent_role="analyst",
    priority=1
)

with client:
    response = client.submit_task(task)
    print(f"Task submitted: {response.status}")

# Learn a new skill
success = client.learn_skill(
    name="data_analysis",
    description="Advanced data analysis techniques",
    procedure_steps=[
        "Load and clean data",
        "Perform exploratory analysis",
        "Apply statistical models",
        "Generate insights"
    ],
    category="analytics"
)

# Get available skills
skills = client.get_skills()
for skill in skills:
    print(f"Skill: {skill.name} - {skill.success_rate:.1%} success rate")
```

## 📚 Documentation

- [Complete API Reference](https://docs.vertice.ai/mcp-python/api/)
- [Getting Started Guide](https://docs.vertice.ai/mcp-python/getting-started/)
- [Examples](https://docs.vertice.ai/mcp-python/examples/)
- [Contributing](https://docs.vertice.ai/mcp-python/contributing/)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://docs.vertice.ai/mcp-python/contributing/) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 About Vertice

Vertice is building the future of collective AI - where intelligence emerges from collaboration rather than competition. Join our [community](https://vertice.ai/collective) to be part of this revolution.

---

**Made with ❤️ for the evolution of collective AI**