# Building AI Agents for Smarter Networks

## Workshop Exercise Guide

Welcome! This guide contains all nine exercises for the workshop. Work through them sequentially - each builds on concepts from the previous exercises.

---

## Workshop Goals

By the end of this workshop, you will:

1. Understand how to use the OpenAI Agents SDK
2. Learn to segment agent responsibilities effectively
3. Develop system prompting and context injection techniques
4. Build functional agents with tool calling capabilities

---

## Table of Contents

1. [Exercise 1: Generative AI Frameworks Introduction](#exercise-1-generative-ai-frameworks-introduction)
2. [Exercise 2: Agentic Design Patterns](#exercise-2-agentic-design-patterns)
3. [Exercise 3: Segmentation of Responsibilities](#exercise-3-segmentation-of-responsibilities)
4. [Exercise 4: Build User Support Agent](#exercise-4-build-user-support-agent)
5. [Exercise 5: Network Problem Introduction](#exercise-5-network-problem-introduction)
6. [Exercise 6: Build Planning Agent](#exercise-6-build-planning-agent)
7. [Exercise 7: Build Provisioning Agent](#exercise-7-build-provisioning-agent)
8. [Exercise 8: Iterative Improvement](#exercise-8-iterative-improvement)
9. [Exercise 9: Full Workflow Example](#exercise-9-full-workflow-example)

---

## Exercise 1: Generative AI Frameworks Introduction

**Duration**: 20 minutes  
**Type**: Lecture + Discussion

### Learning Objectives

- Understand different AI agent frameworks
- Know when to use each framework
- Develop a basic familarity with building agents

### Framework Comparison

#### LangChain

**Strengths:**

- Large community and plugin ecosystem
- RAG (Retrieval Augmented Generation) support
- Multi-Provider/API support (OpenAI, Anthropic, etc.)
- Complex workflow orchestration

**Best for:**

- Multi-LLM applications
- Document-heavy applications
- Complex data pipelines

#### OpenAI Agents SDK

**Strengths:**

- Small, focused SDK
- Clear, minimal data model
- Easily extensible and mutable

**Best for:**

- Well-defined, small-to-medium applications
- Rapid prototyping
- Clear agent-tool relationships
- This workshop!

### Why OpenAI Agents SDK for This Workshop?

1. **Simpler Learning Curve** - Focus on agent design, not framework complexity
2. **Native Tool Calling** - Clean integration with network simulator
3. **Workflow Management** - Built-in context handling, handoffs, and tool-chaining
4. **Production Ready** - Tested and maintained by OpenAI

### Key Concepts

**Agent**: An AI that can use tools to accomplish tasks
**Tool**: A function the agent can call
**Conversation**: Multi-turn interaction with context
**Instructions**: System prompt that guides agent behavior

### Discussion Questions

1. When is a good idea to accelerate a workflow with an AI agent?
2. What are the trade-offs of using an agent over traditonal menus?
3. How might you integrate and existing piece of software into an AI agent?

---

## Exercise 2: Agentic Design Patterns

**Duration**: 30 minutes  
**Type**: Lecture + Design Activity

### Learning Objectives

- Understand centralized vs decentralized architectures
- Learn when to use each pattern
- Design multi-agent systems effectively

### Centralized Multi-Agent Architecture

```
┌──────────────────────────────┐
│   Orchestrator Agent         │
│   (Central Coordinator)      │
└──────────┬───────────────────┘
           │
     ┌─────┼─────┐
     │     │     │
     ▼     ▼     ▼
  ┌───┐ ┌───┐ ┌───┐
  │ A │ │ B │ │ C │  Specialized Agents
  └───┘ └───┘ └───┘
```

**Characteristics:**

- Single coordinator makes decisions
- Specialized agents report back
- Clear delegation of tasks
- Easier to debug and reason about

**Use When:**

- Clear task hierarchy
- Need global coordination
- Sequential workflows
- Single source of truth needed

**Example**: Service provisioning workflow

- Orchestrator receives user request
- Delegates to Planning Agent
- Delegates to Provisioning Agent
- Returns final result

### Decentralized Multi-Agent Architecture

```
  ┌───┐     ┌───┐
  │ A │────▶│ B │
  └─┬─┘     └─┬─┘
    │         │
    ▼         ▼
  ┌───┐     ┌───┐
  │ C │────▶│ D │
  └───┘     └───┘
```

**Characteristics:**

- Agents communicate peer-to-peer
- No single coordinator
- Emergent behavior
- More complex to reason about

**Use When:**

- No clear hierarchy
- Parallel problem solving
- Distributed decision making
- Resilience to failures

**Example**: Network monitoring

- Multiple monitoring agents watch different regions
- Agents share information
- Decisions emerge from collaboration

### Decision Framework

Ask yourself:

1. **Is there a clear workflow?** → Centralized
2. **Do tasks depend on each other?** → Centralized
3. **Need global state management?** → Centralized
4. **Need resilience to coordinator failure?** → Decentralized
5. **Problem naturally parallel?** → Decentralized

### Design Activity

**Scenario**: Design an agent system for network capacity planning

**Requirements**:

- Monitor network utilization
- Predict future capacity needs
- Recommend upgrades
- Execute capacity changes

**Task**: Draw your architecture (centralized or decentralized) and justify your choice.

**Things to consider**:

- How do agents share information?
- Who makes final decisions?
- What happens if an agent fails?
- How do you test the system?

### Discussion

Share your designs with the group. Compare approaches.

---

## Exercise 3: Segmentation of Responsibilities

**Duration**: 25 minutes  
**Type**: Lecture + Analysis

### Learning Objectives

- Learn to divide agent responsibilities effectively
- Understand domain vs task segmentation
- Avoid common anti-patterns

### Segmentation Strategies

#### 1. Domain-Based Segmentation

Divide by business domains or knowledge areas.

**Example**:

- **Network Topology Agent**: Knows about nodes, edges, connections
- **Capacity Agent**: Knows about utilization, violations, planning
- **Service Agent**: Knows about provisioning, lifecycle, SLAs

**Pros:**

- Clear expertise boundaries
- Easy to add new domains
- Specialists can be optimized independently

**Cons:**

- May need coordination across domains
- Potential duplication of knowledge

#### 2. Task-Based Segmentation

Divide by workflow tasks.

**Example**:

- **Planning Agent**: Computes routes, checks feasibility
- **Provisioning Agent**: Creates services, validates results
- **Monitoring Agent**: Tracks health, detects issues

**Pros:**

- Clear workflow mapping
- Easy to follow execution path
- Natural checkpoints between stages

**Cons:**

- Agents may need multiple knowledge domains
- Can lead to monolithic agents

#### 3. Hybrid Segmentation

Combine both approaches.

**Example**:

- **Planning Agent**: Task (planning) + Domain (routing knowledge)
- **Provisioning Agent**: Task (provisioning) + Domain (service API)
- **Topology Expert**: Domain only (consulted by other agents)

### Our Workshop Architecture

We'll use **task-based segmentation** with domain expertise:

```
User Request
     │
     ▼
┌─────────────────┐
│ Support Agent   │  No tools, just documentation
│ (Exercise 4)    │  Helps users understand system
└─────────────────┘

User Service Request
     │
     ▼
┌─────────────────┐
│ Planning Agent  │  Tools: get_nodes(), compute_route()
│ (Exercise 6)    │  Finds viable path
└─────────┬───────┘
          │ Path
          ▼
┌─────────────────┐
│ Provisioning    │  Tools: create_service()
│ Agent (Ex. 7)   │  Provisions on network
└─────────────────┘
```

**Why this works**:

- Clear task boundaries (plan vs provision)
- Minimal inter-agent communication
- Easy to test independently
- Natural workflow progression

### Anti-Patterns to Avoid

#### ❌ God Agent

```python
class NetworkGodAgent:
    """Does everything - planning, provisioning, monitoring, etc."""
```

**Problem**: Too complex, hard to maintain, slow to execute

#### ❌ Chatty Agents

```python
# Agent A calls Agent B which calls Agent C which calls Agent A...
```

**Problem**: Circular dependencies, hard to debug, slow

#### ❌ Overlapping Responsibilities

```python
class PlanningAgent:
    def provision_service(self):  # Wait, this isn't planning!
```

**Problem**: Unclear boundaries, testing difficulty

#### ❌ Tool Sprawl

```python
class SimpleAgent:
    tools = [tool1, tool2, ..., tool50]  # 50 tools!
```

**Problem**: Agent gets confused, slow tool selection

### Best Practices

✅ **Single Responsibility**: Each agent has one clear job
✅ **Minimal Tools**: Give agents only what they need
✅ **Clear Interfaces**: Well-defined inputs and outputs
✅ **Independent Testing**: Each agent testable alone
✅ **Obvious Names**: Name reflects responsibility

### Activity: Analyze This Design

Given this agent:

```python
class NetworkAgent:
    """Handles all network operations."""
    tools = [
        get_nodes, get_edges, get_services,
        create_service, delete_service,
        compute_route, check_capacity,
        send_email, log_event, generate_report
    ]
```

**Questions**:

1. What responsibilities does this agent have?
2. How would you split it?
3. What would you name the new agents?
4. Which tools would each agent get?

---

## Exercise 4: Build User Support Agent

**Duration**: 45 minutes  
**Type**: Hands-on Coding

### Learning Objectives

- Create an agent without tools
- Practice prompt engineering
- Implement context management
- Handle multi-turn conversations

### Background

The support agent helps workshop participants:

- Understand the network simulator
- Learn SDK usage
- Get hints for exercises
- Troubleshoot common issues

**Key Constraint**: No tools! This agent uses only its knowledge and context.

### Part A: Understanding the Agent Structure (10 min)

Open `templates/support_agent_starter.py`:

```python
from agents import Agent, Runner
import os

# Load documentation
WORKSHOP_DOCS = """
[Documentation about network simulator, SDK, exercises]
"""

# Create agent
support_agent = Agent(
    name="WorkshopSupportAgent",
    instructions="You are a helpful workshop assistant...",  # TODO: Improve this!
    model="gpt-4o-mini"
    # Note: No tools parameter - this agent is conversation-only
)
```

**Key components**:

1. **Documentation**: Embedded in system prompt
2. **Instructions**: How the agent should behave
3. **No tools**: Pure conversation-based help

### Part B: Improve the System Prompt (15 min)

Your task: Make the agent more helpful by improving the instructions.

**Requirements**:

- Knows about the network simulator (48 nodes, 200 edges)
- Can explain SDK methods
- Gives exercise hints without full solutions
- Stays in scope (doesn't pretend to have tools)

**Example improvements**:

```python
instructions="""
You are a helpful workshop assistant for "Building AI Agents for Smarter Networks".

Your role:
- Help participants understand the network simulator and SDK
- Provide hints and guidance for exercises
- Explain concepts clearly with examples
- Stay encouraging and patient

About the network:
- 48 nodes across eastern US
- ~200 bidirectional edges
- Real geographic distances
- Capacity constraints (nodes and edges)

SDK key methods:
- client.get_nodes() - retrieve network nodes
- client.compute_route() - find paths with A* algorithm
- client.create_service() - provision services
[Add more...]

Guidelines:
- Give hints, not complete solutions
- If asked about tools, explain the agent doesn't have them
- For code questions, show small examples
- Encourage experimentation

What you DON'T do:
- Execute code or call APIs
- Access the actual network
- Provide complete exercise solutions
"""
```

### Part C: Add Context Management (10 min)

Handle context by including relevant documentation:

```python
def get_relevant_context(query: str) -> str:
    """Return documentation relevant to the query."""
    query_lower = query.lower()

    contexts = {
        "node": NODE_DOCUMENTATION,
        "edge": EDGE_DOCUMENTATION,
        "route": ROUTING_DOCUMENTATION,
        "service": SERVICE_DOCUMENTATION,
        "exercise": EXERCISE_HINTS,
    }

    # Simple keyword matching
    for keyword, context in contexts.items():
        if keyword in query_lower:
            return context

    return GENERAL_DOCUMENTATION
```

### Part D: Test Your Agent (10 min)

Test with these queries:

```python
from agents import Runner

# Test 1: Basic network info
result = Runner.run_sync(support_agent, "How many nodes are in the network?")
print(result.final_output)

# Test 2: SDK usage
result = Runner.run_sync(support_agent, "How do I find a route between two nodes?")
print(result.final_output)

# Test 3: Exercise hint
result = Runner.run_sync(support_agent, "I'm stuck on Exercise 6. Can you help?")
print(result.final_output)

# Test 4: Follow-up questions
result = Runner.run_sync(support_agent, "What is the Planning Agent supposed to do?")
print(result.final_output)
```

### Success Criteria

Your agent should:

- Answer network topology questions correctly
- Explain SDK methods with examples
- Provide helpful hints for exercises
- Maintain context across conversation turns
- Admit when it doesn't have tools/access

### Bonus Challenges

1. Add conversation memory management
2. Implement query classification to route to best documentation
3. Add code example generation
4. Track what topics the user has asked about

### Key Takeaways

- Agents can be useful without tools
- System prompts are crucial for agent behavior
- Context management improves relevance
- Testing is essential

---

## Exercise 5: Network Problem Introduction

**Duration**: 30 minutes  
**Type**: Lecture + Exploration

### Learning Objectives

- Understand the network topology
- Learn network data structures
- Explore SDK capabilities
- Prepare for agent building

### The Network Problem

**Scenario**: You manage a telecommunications network across the eastern United States. You need to:

1. Find viable paths between endpoints
2. Check capacity constraints
3. Provision services
4. Monitor network health

### Network Topology

**Geographic Coverage**: Eastern US (48 cities)

- Major hubs: NYC, Boston, Philadelphia, Washington DC, Atlanta, Miami
- Secondary cities: Albany, Pittsburgh, Richmond, Charleston, etc.
- Real lat/lon coordinates

**Connection Model**:

- Bidirectional edges between nodes
- Variable capacity (50-100 Gbps typical)
- Geographic distance matters
- Current utilization ~6%

### Data Structures

#### Node Object

```python
node.uuid = "550e8400-e29b-41d4-a716-446655440000"
node.name = "Albany-NY"
node.latitude = 42.6526
node.longitude = -73.7562
node.vendor = "Suomi Networks"
node.capacity_gbps = 454.0
node.free_capacity_gbps = 449.5  # Available bandwidth
```

#### Edge Object

```python
edge.uuid = "ec4250e0-..."
edge.node1_uuid = "550e8400-..."
edge.node2_uuid = "6ba7b810-..."
edge.capacity_gbps = 69.7
```

#### Service Object

```python
service.uuid = "service-123"
service.name = "Service Albany to Boston"
service.source_node_uuid = "550e8400-..."
service.destination_node_uuid = "6ba7b810-..."
service.demand_gbps = 5.0
service.hop_count = 2
service.path_node_uuids = ["550e8400-...", "middle-...", "6ba7b810-..."]
service.path_edge_uuids = ["edge1-...", "edge2-..."]
service.total_distance_km = 257.3
```

### Available SDK Functions

See [NETWORK_REFERENCE.md](NETWORK_REFERENCE.md) for complete details.

**Key functions you'll use:**

1. `client.get_nodes()` - Get all network nodes
2. `client.get_edges()` - Get all connections
3. `client.compute_route()` - A\* pathfinding with capacity check
4. `client.create_service()` - Provision a service
5. `client.get_edge_utilization()` - Check capacity usage
6. `client.get_capacity_violations()` - Find oversubscribed edges

### Exploration Activity

Run this exploration script:

```python
from network_simulator_client import NetworkSimulatorClient

with NetworkSimulatorClient(base_url="http://localhost:8003") as client:
    # 1. Network overview
    stats = client.get_database_stats()
    print(f"Network: {stats.nodes} nodes, {stats.edges} edges, {stats.services} services")

    # 2. Examine nodes
    nodes = client.get_nodes()
    print(f"\nSample nodes:")
    for node in nodes[:5]:
        print(f"  {node.name}: {node.capacity_gbps:.0f} Gbps ({node.free_capacity_gbps:.0f} free)")

    # 3. Find a route
    route = client.compute_route(nodes[0].uuid, nodes[-1].uuid, demand_gbps=5.0)
    print(f"\nSample route from {nodes[0].name} to {nodes[-1].name}:")
    print(f"  Distance: {route.total_distance_km:.1f} km")
    print(f"  Hops: {route.hop_count}")
    print(f"  Min capacity: {route.min_available_capacity:.1f} Gbps")
    print(f"  Computation time: {route.computation_time_ms:.2f} ms")

    # 4. Check network health
    violations = client.get_capacity_violations()
    high_util = client.get_high_utilization_edges(threshold_pct=80.0)
    print(f"\nNetwork health:")
    print(f"  Capacity violations: {len(violations)}")
    print(f"  High utilization edges (≥80%): {len(high_util)}")
```

### Capacity Constraints

**Why they matter**:

- Can't route more traffic than edge capacity
- Must check available capacity before provisioning
- Services consume capacity on all edges in their path

**Example**:

- Edge has 100 Gbps capacity
- Currently 60 Gbps used (60% utilization)
- Can add up to 40 Gbps more services
- Adding a 50 Gbps service would violate capacity

### Routing Algorithm

The network uses **A\* pathfinding**:

- Finds shortest geographic path
- Respects capacity constraints
- Very fast (~0.6ms computation time)
- Returns complete path with all intermediate nodes

**What it does**:

1. Start at source node
2. Consider all neighbors
3. Pick next node based on distance + heuristic
4. Only use edges with enough capacity
5. Continue until reaching destination
6. Return ordered list of nodes and edges

---

## Exercise 6: Build Planning Agent

**Duration**: 60 minutes  
**Type**: Hands-on Coding

### Learning Objectives

- Integrate network tools into an agent
- Implement pathfinding logic
- Handle capacity constraints
- Format agent outputs

### Background

The Planning Agent finds viable paths between network endpoints.

**Input**: Source and destination nodes, bandwidth demand
**Output**: Formatted path with capacity validation
**Tools**: Network query functions

### Part A: Review Starter Code (10 min)

Open `templates/planning_agent_starter.py`:

```python
from agents import Agent, Runner
from network_simulator_client import NetworkSimulatorClient

# TODO: Create tool functions
def get_network_nodes():
    """Get all network nodes."""
    # Your code here
    pass

def find_route(source_uuid: str, destination_uuid: str, demand_gbps: float):
    """Find route between nodes."""
    # Your code here
    pass

# TODO: Create agent
planning_agent = Agent(
    name="PlanningAgent",
    instructions="You find viable paths in the network...",
    model="gpt-4o-mini",
    tools=[get_network_nodes, find_route]  # Add your tools
)
```

### Part B: Implement Network Tools (20 min)

Create tool functions the agent can call:

**Tool 1: Get Network Nodes**

```python
def get_network_nodes():
    """
    Get all network nodes with their details.

    Returns a list of nodes with name, UUID, capacity, and location.
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")
    nodes = client.get_nodes()
    client.close()

    # Format for agent consumption
    result = []
    for node in nodes:
        result.append({
            "uuid": node.uuid,
            "name": node.name,
            "capacity_gbps": node.capacity_gbps,
            "free_capacity_gbps": node.free_capacity_gbps,
            "location": f"{node.latitude}, {node.longitude}"
        })

    return result
```

**Tool 2: Find Route**

```python
def find_route(source_uuid: str, destination_uuid: str, demand_gbps: float = 5.0):
    """
    Find a route between two nodes with capacity check.

    Args:
        source_uuid: UUID of source node
        destination_uuid: UUID of destination node
        demand_gbps: Required bandwidth in Gbps

    Returns:
        Route information with path and capacity details
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        route = client.compute_route(source_uuid, destination_uuid, demand_gbps)

        result = {
            "success": True,
            "path_nodes": route.path_node_uuids,
            "path_edges": route.path_edge_uuids,
            "distance_km": route.total_distance_km,
            "hop_count": route.hop_count,
            "min_capacity_gbps": route.min_available_capacity,
            "computation_time_ms": route.computation_time_ms
        }

        client.close()
        return result

    except Exception as e:
        client.close()
        return {
            "success": False,
            "error": str(e)
        }
```

### Part C: Write Agent Instructions (15 min)

Create clear instructions for the agent:

```python
planning_agent = Agent(
    name="PlanningAgent",
    instructions="""
You are a network planning agent that finds viable paths between network nodes.

Your job:
1. When given source and destination nodes (by name or UUID), find a route
2. Check that the route has sufficient capacity for the required bandwidth
3. Return a clear, well-formatted path description

Tools available:
- get_network_nodes(): Get all nodes in the network
- find_route(source_uuid, dest_uuid, demand_gbps): Compute a route

Process:
1. If given node names, use get_network_nodes() to find their UUIDs
2. Call find_route() with the UUIDs and bandwidth requirement
3. Check if min_capacity_gbps >= demand_gbps
4. Format the output clearly

Output format:
Route from [SOURCE] to [DESTINATION]
- Distance: [X] km
- Hops: [N]
- Min available capacity: [Y] Gbps
- Status: [VIABLE/INSUFFICIENT CAPACITY]
- Path: Node1 → Node2 → Node3 → ...

Be concise and clear. If route finding fails, explain why.
""",
    tools=[get_network_nodes, find_route],
    model="gpt-4o-mini"
)
```

### Part D: Test Your Agent (15 min)

Test with various scenarios:

**Test 1: Simple route by name**

```python
result = Runner.run_sync(
    planning_agent,
    "Find a route from Albany-NY to Boston-MA with 5 Gbps demand"
)
print(result.final_output)
```

**Test 2: Route with UUID**

```python
# Get node UUIDs first
client = NetworkSimulatorClient(base_url="http://localhost:8003")
nodes = client.get_nodes()
source = nodes[0]
dest = nodes[-1]
client.close()

result = Runner.run_sync(
    planning_agent,
    f"Find a route from {source.uuid} to {dest.uuid} with 10 Gbps demand"
)
print(result.final_output)
```

**Test 3: High demand (may fail)**

```python
result = Runner.run_sync(
    planning_agent,
    "Find a route from Albany-NY to Miami-FL with 100 Gbps demand"
)
print(result.final_output)
# Should explain insufficient capacity
```

**Test 4: Different node pairs**

```python
result = Runner.run_sync(
    planning_agent,
    "What nodes are available? Then find a route between two of them"
)
print(result.final_output)
```

### Success Criteria

Your agent should:

- Find routes given node names or UUIDs
- Check capacity constraints
- Return well-formatted paths
- Handle errors gracefully (no route found, etc.)
- Work across multiple conversation turns

### Common Issues & Solutions

**Issue**: Agent doesn't call tools

- Check tool function signatures match expectations
- Ensure docstrings clearly describe what tools do
- Verify tools are in the agent's tools list

**Issue**: Route finding fails

- Check that source and destination UUIDs are valid
- Verify the API is running (curl http://localhost:8003/health)
- Try a smaller demand_gbps value

**Issue**: Agent output is messy

- Improve the output format section in instructions
- Give example outputs
- Ask agent to use specific formatting

### Bonus Challenges

1. Add tool to get node by name (exact match)
2. Implement breadth-first search instead of using compute_route()
3. Find multiple alternative routes
4. Compare routes by different metrics (distance, hops, capacity)

### Key Takeaways

- Tools are functions the agent can call
- Clear docstrings help agent use tools correctly
- Instructions guide agent behavior
- Output formatting requires explicit guidance
- Error handling is crucial

---

## Exercise 7: Build Provisioning Agent

**Duration**: 60 minutes  
**Type**: Hands-on Coding

### Learning Objectives

- Create service provisioning tools
- Parse planning agent output
- Validate before provisioning
- Handle provisioning errors

### Background

The Provisioning Agent creates services on planned paths.

**Input**: Path from Planning Agent, service parameters
**Output**: Provisioned service confirmation
**Tools**: Service creation and validation functions

### Part A: Review Starter Code (10 min)

Open `templates/provisioning_agent_starter.py`:

```python
from agents import Agent, Runner
from network_simulator_client import NetworkSimulatorClient, ServiceCreate
from datetime import datetime

# TODO: Create tool functions
def create_network_service(
    name: str,
    source_uuid: str,
    destination_uuid: str,
    demand_gbps: float,
    path_node_uuids: list,
    path_edge_uuids: list,
    total_distance_km: float
):
    """Provision a service on the network."""
    # Your code here
    pass

def verify_service(service_uuid: str):
    """Verify a service was created successfully."""
    # Your code here
    pass

# TODO: Create agent
provisioning_agent = Agent(
    name="ProvisioningAgent",
    instructions="You provision services on the network...",
    model="gpt-4o-mini",
    tools=[create_network_service, verify_service]
)
```

### Part B: Implement Provisioning Tools (25 min)

**Tool 1: Create Service**

```python
def create_network_service(
    name: str,
    source_uuid: str,
    destination_uuid: str,
    demand_gbps: float,
    path_node_uuids: list,
    path_edge_uuids: list,
    total_distance_km: float
):
    """
    Provision a service on the network.

    Args:
        name: Service name
        source_uuid: Source node UUID
        destination_uuid: Destination node UUID
        demand_gbps: Bandwidth requirement
        path_node_uuids: Ordered list of nodes in path
        path_edge_uuids: Ordered list of edges in path
        total_distance_km: Total path distance

    Returns:
        Service creation result with UUID
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        # Create service object
        service_data = ServiceCreate(
            name=name,
            source_node_uuid=source_uuid,
            destination_node_uuid=destination_uuid,
            demand_gbps=demand_gbps,
            routing_stage="stage_a",
            path_node_uuids=path_node_uuids,
            path_edge_uuids=path_edge_uuids,
            total_distance_km=total_distance_km,
            service_timestamp=datetime.utcnow().isoformat() + "Z"
        )

        # Provision service
        created_service = client.create_service(service_data)

        result = {
            "success": True,
            "service_uuid": created_service.uuid,
            "name": created_service.name,
            "hop_count": created_service.hop_count
        }

        client.close()
        return result

    except Exception as e:
        client.close()
        return {
            "success": False,
            "error": str(e)
        }
```

**Tool 2: Verify Service**

```python
def verify_service(service_uuid: str):
    """
    Verify a service exists and get its details.

    Args:
        service_uuid: UUID of service to verify

    Returns:
        Service details or error
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        service = client.get_service(service_uuid)

        result = {
            "exists": True,
            "name": service.name,
            "source": service.source_node_uuid,
            "destination": service.destination_node_uuid,
            "demand_gbps": service.demand_gbps,
            "hop_count": service.hop_count,
            "distance_km": service.total_distance_km
        }

        client.close()
        return result

    except Exception as e:
        client.close()
        return {
            "exists": False,
            "error": str(e)
        }
```

**Tool 3: Delete Service (cleanup)**

```python
def delete_network_service(service_uuid: str):
    """
    Delete a service to free up capacity.

    Args:
        service_uuid: UUID of service to delete

    Returns:
        Deletion result
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        client.delete_service(service_uuid)
        client.close()
        return {"success": True, "message": "Service deleted"}
    except Exception as e:
        client.close()
        return {"success": False, "error": str(e)}
```

### Part C: Write Agent Instructions (15 min)

```python
provisioning_agent = Agent(
    name="ProvisioningAgent",
    instructions="""
You are a network provisioning agent that creates services on planned paths.

Your job:
1. Parse path information from the planning agent
2. Validate all required parameters are present
3. Provision the service on the network
4. Verify successful provisioning

Tools available:
- create_network_service(...): Provision a service
- verify_service(uuid): Check service was created
- delete_network_service(uuid): Remove a service

Process:
1. Extract required parameters from the user's request:
   - Service name
   - Source and destination UUIDs
   - Demand in Gbps
   - Path nodes (list of UUIDs)
   - Path edges (list of UUIDs)
   - Total distance
2. Validate path structure (nodes = edges + 1)
3. Call create_network_service()
4. If successful, verify with verify_service()
5. Report results clearly

Output format:
Service provisioned successfully!
- Service UUID: [UUID]
- Name: [NAME]
- Path: [N] hops, [X] km
- Demand: [Y] Gbps
- Status: Active

If provisioning fails, explain why clearly.
""",
    tools=[create_network_service, verify_service, delete_network_service],
    model="gpt-4o-mini"
)
```

### Part D: Test Your Agent (10 min)

**Test 1: Provision service from planning output**

First, get a route from planning agent:

```python
route_result = Runner.run_sync(
    planning_agent,
    "Find a route from Albany-NY to Boston-MA with 5 Gbps demand"
)
print("Planning Agent Output:")
print(route_result.final_output)
```

Then provision:

```python
provision_request = f"""
Provision a service called 'Workshop-Test-Service' using this plan:
{route_result.final_output}

Service requirements:
- Demand: 5 Gbps
- Name: Workshop-Test-Service
"""

result = Runner.run_sync(provisioning_agent, provision_request)
print("\nProvisioning Agent Output:")
print(result.final_output)
```

**Test 2: Verify service**

```python
# Extract service UUID from response
# Then verify
result = Runner.run_sync(
    provisioning_agent,
    f"Verify service {service_uuid}"
)
print(result.final_output)
```

**Test 3: Cleanup**

```python
result = Runner.run_sync(
    provisioning_agent,
    f"Delete service {service_uuid}"
)
print(result.final_output)
```

### Success Criteria

Your agent should:

- Parse planning agent output correctly
- Validate path structure before provisioning
- Successfully create services
- Verify provisioning completed
- Handle errors gracefully
- Support cleanup operations

### Common Issues & Solutions

**Issue**: Can't parse planning output

- Make planning agent output more structured
- Add example parsing to provisioning agent instructions
- Use JSON format for inter-agent communication

**Issue**: Provisioning fails with validation error

- Check that path_nodes length = path_edges length + 1
- Verify all UUIDs are valid
- Ensure source/dest match first/last nodes in path

**Issue**: Service created but not verified

- Add delay before verification
- Check service UUID is correct
- Verify API connectivity

### Bonus Challenges

1. Add capacity pre-check before provisioning
2. Implement rollback on provisioning failure
3. Support batch provisioning of multiple services
4. Add service lifecycle management (pause, resume, modify)

### Key Takeaways

- Provisioning requires careful validation
- Inter-agent communication needs structure
- Error handling prevents partial states
- Verification confirms operations succeeded

---

## Exercise 8: Iterative Improvement

**Duration**: 45 minutes  
**Type**: Guided Practice

### Learning Objectives

- Improve agent prompts iteratively
- Optimize data flows
- Mitigate tool calling errors
- Test and debug agents

### Part A: Prompt Refinement (15 min)

#### Iteration 1: Too Vague

```python
instructions = "You help with networking."
```

**Problems**: Agent doesn't know what to do, how to do it, or when

#### Iteration 2: Too Specific

```python
instructions = """
First call get_nodes.
Then find node with name matching user input.
Then call find_route with those UUIDs.
Then format output with exactly 3 lines.
Line 1 must be 'Route found'
Line 2 must show distance
...
"""
```

**Problems**: Too rigid, can't handle variations, no flexibility

#### Iteration 3: Balanced

```python
instructions = """
You find network routes. When asked to route between nodes:
1. Identify source and destination (names or UUIDs)
2. Use get_nodes() if you need to look up names
3. Call find_route() with appropriate parameters
4. Return a clear summary of the route

Be helpful and adapt to the user's style.
"""
```

**Problems**: Just right! Clear but flexible.

#### Your Turn

Refine one of your agent prompts. Test before and after.

### Part B: Data Flow Optimization (15 min)

#### Anti-Pattern: Chatty Flow

```python
# Agent makes 10 separate API calls
for node in all_nodes:
    details = get_node_details(node.uuid)  # Slow!
```

#### Better: Batch Operations

```python
# Agent gets all data at once
all_nodes_with_details = get_all_nodes()  # Fast!
```

#### Anti-Pattern: Redundant Calls

```python
# Agent calls same function repeatedly
node1 = get_node(uuid)
# ... later ...
node1_again = get_node(uuid)  # Wasteful!
```

#### Better: Context Preservation

```python
# Agent remembers previous results
# Use conversation context or caching
```

#### Your Turn

Analyze your agents. How many tool calls do they make? Can you reduce it?

### Part C: Tool Calling Error Mitigation (15 min)

Common issues and solutions:

#### Issue 1: Wrong Parameter Types

```python
# Agent tries to call:
find_route("Albany-NY", "Boston-MA", ...)
# But expects UUIDs!
```

**Solution**: Clear docstrings

```python
def find_route(source_uuid: str, destination_uuid: str, demand_gbps: float):
    """
    Find route between nodes.

    Args:
        source_uuid: Node UUID (NOT name), example: "550e8400-..."
        destination_uuid: Node UUID (NOT name)
        demand_gbps: Bandwidth in Gbps (float), example: 5.0
    """
```

#### Issue 2: Missing Parameters

```python
# Agent calls:
create_service(name="test", source="...")
# Missing required params!
```

**Solution**: Required parameter documentation

```python
"""
ALL of these parameters are REQUIRED:
- name: Service name (string)
- source_uuid: Source node UUID
- ...
"""
```

#### Issue 3: Invalid Values

```python
# Agent calls:
find_route(source, dest, demand_gbps=-10)  # Negative!
```

**Solution**: Validation + instructions

```python
# In function:
if demand_gbps <= 0:
    return {"error": "Demand must be positive"}

# In instructions:
"demand_gbps must be a positive number, typically 5-100 Gbps"
```

#### Your Turn

Add better validation to your tools. Test with bad inputs.

---

## Exercise 9: Full Workflow Example

**Duration**: 45 minutes  
**Type**: End-to-End Demo + Practice

### Learning Objectives

- Integrate all agents into a workflow
- Handle end-to-end service provisioning
- Practice with real scenarios
- See the complete picture

### The Complete Workflow

```
User: "I need a 10 Gbps link from New York to Miami"
  │
  ▼
┌─────────────────────┐
│  1. Support Agent   │ (Optional: Help user understand)
│  (No tools)         │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│  2. Planning Agent  │ Tools: get_nodes, find_route
│  Find viable path   │ Output: Path with nodes and edges
└──────────┬──────────┘
           │ Path
           ▼
┌─────────────────────┐
│  3. Provisioning    │ Tools: create_service, verify
│  Create service     │ Output: Service UUID
└──────────┬──────────┘
           │
           ▼
        Success!
```

### Scenario 1: Simple Provisioning

**User Request**: "Create a 5 Gbps service from Albany-NY to Boston-MA"

**Step 1 - Planning**:

```python
planning_result = Runner.run_sync(
    planning_agent,
    "Find a route from Albany-NY to Boston-MA with 5 Gbps demand"
)
print("=== PLANNING ===")
print(planning_result.final_output)
# Expected: Route with nodes, edges, distance, capacity
```

**Step 2 - Provisioning**:

```python
provisioning_request = f"""
Provision a service called 'Albany-Boston-Service' using this plan:
{planning_result.final_output}
"""

provisioning_result = Runner.run_sync(provisioning_agent, provisioning_request)
print("\n=== PROVISIONING ===")
print(provisioning_result.final_output)
# Expected: Service UUID, confirmation
```

**Step 3 - Verification**:

```python
# Extract service UUID from response
# Verify in network
client = NetworkSimulatorClient(base_url="http://localhost:8003")
service = client.get_service(service_uuid)
print(f"\n=== VERIFICATION ===")
print(f"Service {service.name} is active")
print(f"  Consuming {service.demand_gbps} Gbps on {service.hop_count} hops")
client.close()
```

### Scenario 2: High-Demand Service

**User Request**: "I need a 50 Gbps connection from NYC to Miami"

**Expected behavior**:

- Planning agent finds route (may fail if insufficient capacity)
- If route found, provisioning agent creates service
- If route not found, explain capacity limitation

Try it:

```python
result = Runner.run_sync(
    planning_agent,
    "Find a route from New-York-NY to Miami-FL with 50 Gbps demand"
)
print(result.final_output)

# If successful, provision
# If failed, explain to user why
```

### Scenario 3: Multiple Services

**User Request**: "Provision three 5 Gbps services: Albany to Boston, NYC to Philadelphia, and Washington to Richmond"

**Your task**: Create a loop or batch process to handle this.

Pseudo-code:

```python
requests = [
    ("Albany-NY", "Boston-MA", 5.0),
    ("New-York-NY", "Philadelphia-PA", 5.0),
    ("Washington-DC", "Richmond-VA", 5.0)
]

results = []
for source, dest, demand in requests:
    # Plan
    route = Runner.run_sync(
        planning_agent,
        f"Route from {source} to {dest}, {demand} Gbps"
    )

    # Provision
    service = Runner.run_sync(
        provisioning_agent,
        f"Provision service from {source} to {dest}..."
    )

    results.append(service.final_output)

# Report all results
```

### Scenario 4: Network Analysis Before Provisioning

**User Request**: "Find the best route from Albany to Miami"

"Best" could mean:

- Shortest distance
- Fewest hops
- Most available capacity
- Lowest utilization edges

**Your task**: Modify planning agent to consider multiple criteria.

### Activity: Build Your Own Scenario

Create a scenario that:

1. Uses both agents
2. Requires some decision making
3. Has success and failure cases
4. Demonstrates the value of agents

Example ideas:

- "Find routes for 10 services with minimal overlap"
- "Provision services to balance network load"
- "Find alternative routes when primary is congested"

### Integration Patterns

#### Pattern 1: Sequential (Simple)

```python
from agents import Runner

plan = Runner.run_sync(planning_agent, user_request)
result = Runner.run_sync(
    provisioning_agent,
    f"Execute this plan: {plan.final_output}"
)
```

#### Pattern 2: Validation Loop

```python
plan = Runner.run_sync(planning_agent, user_request)

# Validate plan
if validate_plan(plan.final_output):
    result = Runner.run_sync(
        provisioning_agent,
        f"Execute: {plan.final_output}"
    )
else:
    plan = Runner.run_sync(
        planning_agent,
        f"That plan failed. Try again: {user_request}"
    )
```

#### Pattern 3: Orchestrator

```python
from agents import Runner

class WorkflowOrchestrator:
    def provision_service(self, source, dest, demand):
        # 1. Plan
        plan = Runner.run_sync(
            self.planning_agent,
            f"Route {source} to {dest}, {demand} Gbps"
        )

        # 2. Check
        if not self.is_valid_plan(plan.final_output):
            return {"error": "No valid route"}

        # 3. Provision
        result = Runner.run_sync(
            self.provisioning_agent,
            f"Provision: {plan.final_output}"
        )

        # 4. Verify
        if self.verify_provisioning(result.final_output):
            return {"success": True, "service": result.final_output}
        else:
            return {"error": "Provisioning failed"}
```

### Success Criteria

By the end of this exercise, you should be able to:

- Plan and provision services end-to-end
- Handle success and failure cases
- Coordinate multiple agents
- Validate intermediate results
- Explain what each agent does and why

### Key Takeaways

- Agents work best with clear responsibilities
- Inter-agent communication needs structure
- Validation between stages prevents errors
- Real workflows need error handling
- Testing each component helps debug the whole

---

## Conclusion & Next Steps

Workshop topics covered:

- How to use OpenAI Agents SDK
- Agentic design patterns
- Segmentation of responsibilities
- Tool calling and function integration
- Prompt engineering for agents
- Multi-agent workflows

### What You've Built

1. Support Agent - Helps users without tools
2. Planning Agent - Finds network routes with capacity checking
3. Provisioning Agent - Creates services on the network
4. Full Workflow - End-to-end service provisioning

### Going Further

Ideas for extension:

- Add monitoring agent (track capacity over time)
- Build optimization agent (improve network efficiency)
- Create failure recovery agent (reroute on failures)
- Implement policy agent (enforce business rules)

Advanced topics to explore:

- Async agents for parallel operations
- Agent memory and learning
- Multi-model agents (using different LLMs)
- Agent benchmarking and evaluation

### Resources

- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- Network Simulator API: http://localhost:8003/docs
- SDK Documentation: ../README.md

---
