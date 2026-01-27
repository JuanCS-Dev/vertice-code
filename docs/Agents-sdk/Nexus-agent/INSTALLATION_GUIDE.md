# NEXUS Meta-Agent - Installation & Usage Guide

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Google Cloud Platform** account with:
   - Project created
   - Vertex AI API enabled
   - Firestore database created
   - Service account with appropriate permissions
3. **Vertice MCP** setup (your existing installation)
4. **Gemini 3 API** access

### Installation Steps

#### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv-nexus
source venv-nexus/bin/activate  # On Windows: venv-nexus\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Vertice MCP SDK
pip install -e /path/to/vertice-mcp  # Or from your package repository
```

#### 2. Configure Google Cloud

```bash
# Set up authentication
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable monitoring.googleapis.com
```

#### 3. Set Environment Variables

Create a `.env` file:

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Vertice MCP
MCP_ENDPOINT=https://mcp.vertice.ai
MCP_API_KEY=your-api-key-here  # If required

# NEXUS Configuration
NEXUS_GEMINI_MODEL=gemini-3-pro  # or gemini-3-flash
NEXUS_DEEP_THINK=false
NEXUS_CONTEXT_WINDOW=1000000
```

#### 4. Initialize Firestore Collections

```bash
# Run initialization script
python scripts/init_firestore.py
```

### Basic Usage

#### Running NEXUS

```bash
# Standard mode
python nexus_agent.py

# With Deep Think enabled
NEXUS_DEEP_THINK=true python nexus_agent.py

# Custom configuration
python nexus_agent.py --config config/nexus_config.yaml
```

#### Configuration File (nexus_config.yaml)

```yaml
nexus:
  project_id: your-gcp-project-id
  region: us-central1
  gemini_model: gemini-3-pro
  deep_think_mode: false
  context_window: 1000000

  evolutionary:
    population: 50
    island_count: 5
    mutation_rate: 0.15

  monitoring:
    reflection_frequency: 10
    healing_check_interval: 60
    evolution_cycle_hours: 24

mcp:
  endpoint: https://mcp.vertice.ai
  api_key: ${MCP_API_KEY}
  timeout: 30.0
```

## 📊 Usage Examples

### Example 1: Basic Autonomous Operation

```python
import asyncio
from vertice_mcp.types import MCPClientConfig
from nexus_agent import NexusMetaAgent, NexusConfig

async def main():
    # Configure
    mcp_config = MCPClientConfig(
        endpoint="https://mcp.vertice.ai",
        api_key="your-api-key"
    )

    nexus_config = NexusConfig(
        project_id="your-project",
        gemini_model="gemini-3-pro"
    )

    # Start NEXUS
    nexus = NexusMetaAgent(mcp_config, nexus_config)
    await nexus.start()

asyncio.run(main())
```

### Example 2: Manual Reflection

```python
from nexus_agent import MetacognitiveEngine, NexusConfig

async def reflect_on_task():
    config = NexusConfig(project_id="your-project")
    engine = MetacognitiveEngine(config)

    task = {
        'id': 'task-123',
        'description': 'Deploy new feature',
        'agent_role': 'devops'
    }

    outcome = {
        'success': True,
        'execution_time': 45.2,
        'quality_score': 0.92
    }

    insight = await engine.reflect_on_task_outcome(
        task,
        outcome,
        system_state
    )

    print(f"Learning: {insight.learning}")
    print(f"Action: {insight.action}")
    print(f"Confidence: {insight.confidence}")
```

### Example 3: Evolutionary Optimization

```python
from nexus_agent import EvolutionaryCodeOptimizer, NexusConfig

async def evolve_agent():
    config = NexusConfig(project_id="your-project")
    optimizer = EvolutionaryCodeOptimizer(config)

    best_solution = await optimizer.evolve_agent_code(
        target_agent="coder_agent",
        optimization_goals=[
            "improve_performance",
            "reduce_errors",
            "enhance_maintainability"
        ],
        generations=50
    )

    print(f"Best fitness: {best_solution.fitness_scores['aggregate']}")
    print(f"Best code:\n{best_solution.code}")
```

### Example 4: Self-Healing Demonstration

```python
from nexus_agent import SelfHealingOrchestrator, NexusConfig

async def demonstrate_healing():
    config = NexusConfig(project_id="your-project")
    healer = SelfHealingOrchestrator(config)

    # Simulate an anomaly
    anomaly = {
        'type': 'high_error_rate',
        'severity': 0.85,
        'metric': 'error_rate',
        'value': 0.042,
        'threshold': 0.03
    }

    # Autonomous healing
    await healer.autonomous_heal(anomaly)
```

## 🔧 Configuration Options

### NexusConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | str | required | GCP project ID |
| `region` | str | "us-central1" | GCP region |
| `gemini_model` | str | "gemini-3-pro" | Gemini model to use |
| `deep_think_mode` | bool | False | Enable Deep Think reasoning |
| `context_window` | int | 1000000 | Token context window |
| `evolutionary_population` | int | 50 | Population size per island |
| `island_count` | int | 5 | Number of evolutionary islands |
| `mutation_rate` | float | 0.15 | Mutation probability |
| `reflection_frequency` | int | 10 | Tasks between reflections |
| `healing_check_interval` | int | 60 | Seconds between health checks |
| `evolution_cycle_hours` | int | 24 | Hours between evolution cycles |

### Gemini 3 Models

- **gemini-3-pro**: Best for complex reasoning, Deep Think
- **gemini-3-flash**: Fast, cost-effective for high-volume operations
- **gemini-3-ultra**: Maximum capabilities (premium tier)

### Deep Think Mode

Enable Deep Think for:
- Complex problem diagnosis
- Multi-step reasoning
- Novel algorithm discovery
- Strategic planning

⚠️ **Note**: Deep Think mode increases latency and cost but provides superior reasoning.

## 📈 Monitoring & Observability

### View Real-time Metrics

```python
from nexus_agent import NexusMetaAgent

async def check_status():
    nexus = NexusMetaAgent(mcp_config, nexus_config)

    print(f"Total Healings: {nexus.system_state.total_healings}")
    print(f"Total Optimizations: {nexus.system_state.total_optimizations}")
    print(f"Evolutionary Generation: {nexus.system_state.evolutionary_generation}")
    print(f"Agent Health: {nexus.system_state.agent_health}")
```

### Firestore Collections

NEXUS stores data in these Firestore collections:

- `metacognitive_insights`: Reflection insights
- `healing_actions`: Self-healing history
- `evolutionary_populations`: Evolution candidates
- `system_states`: System state snapshots

### GCP Monitoring

Create custom dashboards to track:
- Healing success rate
- Evolution fitness scores
- Reflection confidence trends
- System health metrics

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/
```

### Run Integration Tests

```bash
pytest tests/integration/ --integration
```

### Test Individual Components

```bash
# Test metacognitive engine
pytest tests/test_metacognitive.py

# Test self-healing
pytest tests/test_healing.py

# Test evolution
pytest tests/test_evolution.py
```

## 🔒 Security Best Practices

1. **Service Account Permissions**: Use least-privilege principle
   ```bash
   gcloud iam service-accounts create nexus-agent
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:nexus-agent@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

2. **API Key Management**: Use Secret Manager
   ```bash
   echo -n "your-api-key" | gcloud secrets create mcp-api-key --data-file=-
   ```

3. **Network Security**: Configure VPC and firewall rules

4. **Audit Logging**: Enable Cloud Audit Logs
   ```bash
   gcloud logging read "resource.type=aiplatform.googleapis.com"
   ```

## 🚨 Troubleshooting

### Common Issues

#### "Failed to connect to MCP server"

```bash
# Check endpoint
curl -v https://mcp.vertice.ai/health

# Verify API key
echo $MCP_API_KEY
```

#### "Gemini API authentication failed"

```bash
# Re-authenticate
gcloud auth application-default login

# Check quota
gcloud alpha quotas describe aiplatform.googleapis.com/generate_content
```

#### "Firestore permission denied"

```bash
# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@domain.com" \
  --role="roles/datastore.user"
```

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

nexus = NexusMetaAgent(mcp_config, nexus_config)
```

### Performance Optimization

**For faster evolution:**
- Use `gemini-3-flash` instead of `gemini-3-pro`
- Reduce `evolutionary_population` to 25
- Decrease `island_count` to 3

**For deeper reasoning:**
- Enable `deep_think_mode`
- Increase `reflection_frequency`
- Use `gemini-3-ultra` for critical decisions

## 📚 Additional Resources

- [Gemini 3 Documentation](https://ai.google.dev/gemini-api/docs)
- [Vertex AI Python SDK](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Vertice MCP API Reference](https://docs.vertice.ai/mcp/)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Support

- GitHub Issues: [Report bugs](https://github.com/vertice-ai/nexus/issues)
- Discord: [Join community](https://discord.gg/vertice-ai)
- Email: collective@vertice.ai

---

**Built with 🧬 by Vertice AI Collective**
**For the Evolution of Collective AI**
