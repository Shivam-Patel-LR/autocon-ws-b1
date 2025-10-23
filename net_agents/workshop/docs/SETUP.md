# Workshop Setup Guide
## Building AI Agents for Smarter Networks

Welcome to the AI Agents workshop! This guide will help you set up your environment for building intelligent network agents.

---

## Prerequisites

- **Python 3.8 or higher** (3.12 recommended)
- **Git** (for cloning the repository)
- **Docker** and **Docker Compose** (for running the network simulator)
- **Text editor or IDE** (VS Code, PyCharm, or similar)
- **OpenAI API Key** (you'll need this for the agents)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/autocon.git
cd autocon
```

---

## Step 2: Set Up Python Environment

### Option A: Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
cd net_agents
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
uv pip install openai-agents
```

### Option B: Using pip

```bash
cd net_agents
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -e .
pip install openai-agents
```

---

## Step 3: Set Up OpenAI API Key

The OpenAI Agents SDK requires an API key to function.

### Get Your API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (you won't be able to see it again!)

### Configure API Key

Create a `.env` file in the `net_agents/workshop/` directory:

```bash
cd workshop
cat > .env << 'EOF'
OPENAI_API_KEY=your-api-key-here
EOF
```

Replace `your-api-key-here` with your actual API key.

**Important**: Never commit your `.env` file to version control!

---

## Step 4: Start the Network Simulator

The network simulator runs as a Docker container and provides the API that your agents will interact with.

```bash
# Navigate to the network_simulator directory
cd ../../network_simulator

# Build and start the simulator
docker compose up --build -d

# Verify it's running
curl http://localhost:8003/health
```

You should see a response like:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-17T12:00:00Z"
}
```

### Access the API Documentation

Once running, you can explore the API:
- **Swagger UI**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **ReDoc**: [http://localhost:8003/redoc](http://localhost:8003/redoc)

---

## Step 5: Verify Installation

Run this verification script to make sure everything is working:

```python
# Save as verify_setup.py
import os
from network_simulator_client import NetworkSimulatorClient

# Check API connection
try:
    client = NetworkSimulatorClient(base_url="http://localhost:8003")
    health = client.health_check()
    print(f"[OK] Network Simulator API: {health.status}")

    stats = client.get_database_stats()
    print(f"[OK] Network loaded: {stats.nodes} nodes, {stats.edges} edges, {stats.services} services")

    client.close()
except Exception as e:
    print(f"[FAIL] API Connection Failed: {e}")
    print("  Make sure the simulator is running: docker compose up -d")
    exit(1)

# Check OpenAI Agents SDK
try:
    import agents
    print("[OK] OpenAI Agents SDK installed")
except ImportError:
    print("[FAIL] OpenAI Agents SDK not installed")
    print("  Install with: uv pip install openai-agents")
    exit(1)

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("[FAIL] OPENAI_API_KEY not set")
    print("  Create a .env file with your API key")
    exit(1)
else:
    print("[OK] OpenAI API key configured")

print("\nSetup complete! You're ready to start building agents.")
```

Run it:
```bash
cd net_agents/workshop
python verify_setup.py
```

If all checks pass, the setup is complete.

---

## Step 6: Explore the Network Simulator

Before building agents, let's explore what you'll be working with:

```python
from network_simulator_client import NetworkSimulatorClient

with NetworkSimulatorClient(base_url="http://localhost:8003") as client:
    # Get network overview
    stats = client.get_database_stats()
    print(f"Network: {stats.nodes} nodes, {stats.edges} edges")

    # Look at some nodes
    nodes = client.get_nodes()
    print(f"\nFirst 5 nodes:")
    for node in nodes[:5]:
        print(f"  {node.name}: {node.capacity_gbps:.0f} Gbps capacity ({node.vendor})")

    # Check network health
    violations = client.get_capacity_violations()
    if violations:
        print(f"\n[WARNING] {len(violations)} capacity violations detected")
    else:
        print(f"\n[OK] Network is healthy (no capacity violations)")

    # Compute a sample route
    route = client.compute_route(
        source_node_uuid=nodes[0].uuid,
        destination_node_uuid=nodes[-1].uuid,
        demand_gbps=5.0
    )
    print(f"\nSample route: {route.hop_count} hops, {route.total_distance_km:.1f} km")
```

---

## Workshop Structure

The workshop materials are organized as follows:

```
net_agents/workshop/
├── SETUP.md                    # This file
├── NETWORK_REFERENCE.md        # Quick reference for the network simulator
├── EXERCISE_GUIDE.md           # Complete exercise instructions
├── support_agent.py            # Working support agent implementation
├── templates/                  # Starter code for each exercise
│   ├── support_agent_starter.py
│   ├── planning_agent_starter.py
│   ├── provisioning_agent_starter.py
│   └── full_workflow_starter.py
└── solutions/                  # Reference implementations (for instructors)
    ├── support_agent_solution.py
    ├── planning_agent_solution.py
    ├── provisioning_agent_solution.py
    └── full_workflow_solution.py
```

---

## OpenAI Agents SDK Quick Reference

The OpenAI Agents SDK provides a simple framework for building AI agents with tool calling capabilities.

### Basic Agent Structure

```python
from agents import Agent, Runner

# Create an agent
agent = Agent(
    name="MyAgent",
    instructions="You are a helpful assistant...",
    model="gpt-4o-mini"  # or "gpt-4o"
)

# Run the agent
result = Runner.run_sync(agent, "User query here")
print(result.final_output)
```

### Agent with Tools

```python
from agents import Agent, Runner

def my_tool(arg: str) -> str:
    """Tool description that the agent will see."""
    return f"Result for {arg}"

agent = Agent(
    name="ToolAgent",
    instructions="Use tools to help the user...",
    tools=[my_tool],
    model="gpt-4o-mini"
)

# Run with tool
result = Runner.run_sync(agent, "Use the tool with argument 'test'")
print(result.final_output)
```

### Async Usage

```python
import asyncio
from agents import Agent, Runner

async def main():
    result = await Runner.run(agent, "Your prompt here")
    print(result.final_output)

asyncio.run(main())
```

---

## Network Simulator Client Quick Reference

### Basic Operations

```python
from network_simulator_client import NetworkSimulatorClient

client = NetworkSimulatorClient(base_url="http://localhost:8003")

# Get nodes
nodes = client.get_nodes()
node = client.get_node(node_uuid)

# Get edges
edges = client.get_edges()
edge = client.get_edge(edge_uuid)

# Compute routes
route = client.compute_route(source_uuid, dest_uuid, demand_gbps=10.0)

# Manage services
service = client.create_service(service_data)
client.delete_service(service_uuid)

# Monitor capacity
summary = client.get_capacity_summary()
violations = client.get_capacity_violations()

client.close()
```

See [NETWORK_REFERENCE.md](NETWORK_REFERENCE.md) for complete details.

---

## Troubleshooting

### API Connection Fails

**Problem**: `APIConnectionError: Failed to connect to API`

**Solutions**:
- Check if the simulator is running: `docker ps | grep network`
- Start it if needed: `cd network_simulator && docker compose up -d`
- Verify it's healthy: `curl http://localhost:8003/health`
- Check port 8003 isn't being used by another service

### OpenAI API Key Issues

**Problem**: `AuthenticationError` or `API key not found`

**Solutions**:
- Make sure `.env` file exists in `workshop/` directory
- Check the file contains: `OPENAI_API_KEY=sk-...`
- Load it in your code: `from dotenv import load_dotenv; load_dotenv()`
- Verify it's set: `echo $OPENAI_API_KEY` (in terminal)

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'openai_agents'`

**Solutions**:
- Make sure virtual environment is activated
- Install the SDK: `uv pip install openai-agents`
- For network client: `cd net_agents && uv pip install -e .`

### Docker Issues

**Problem**: `Cannot connect to the Docker daemon`

**Solutions**:
- Make sure Docker Desktop is running
- On Linux: `sudo systemctl start docker`
- Check Docker is accessible: `docker ps`

### Port Already in Use

**Problem**: Port 8003 is already in use

**Solutions**:
- Find what's using it: `lsof -i :8003` (Mac/Linux) or `netstat -ano | findstr :8003` (Windows)
- Stop the process or change the port in `docker-compose.yml`

---

## Getting Help

During the workshop:
1. **Use the support agent** - It can answer questions about the network simulator and SDK
2. **Check the documentation** - NETWORK_REFERENCE.md and EXERCISE_GUIDE.md
3. **Ask the instructors** - We're here to help!
4. **Review the solutions** - Available in `solutions/` directory

---

## Next Steps

1. Complete this setup guide
2. Read [NETWORK_REFERENCE.md](NETWORK_REFERENCE.md) to understand the network
3. Start [EXERCISE_GUIDE.md](EXERCISE_GUIDE.md) with Exercise 1
4. Build your first agent

---

## Additional Resources

- **OpenAI Agents SDK Docs**: https://openai.github.io/openai-agents-python/
- **OpenAI API Reference**: https://platform.openai.com/docs/api-reference
- **Network Simulator API Docs**: http://localhost:8003/docs (when running)
- **Network Simulator Client README**: ../README.md

---
