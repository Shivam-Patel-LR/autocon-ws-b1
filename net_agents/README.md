# Network Simulator Client SDK

A comprehensive, production-ready Python client for the Network Simulator API. This SDK provides intuitive interfaces for managing network topology, computing routes, tracking capacity, and creating services. Designed specifically for building AI agents that interact with network infrastructure.

## Features

- **Complete API Coverage**: All 50+ API endpoints fully implemented
- **Type Safety**: Full Pydantic model validation with type hints
- **Error Handling**: Comprehensive exception hierarchy for robust error management
- **Sync & Async Ready**: Built on httpx for both synchronous and asynchronous support
- **Well Documented**: Extensive docstrings, examples, and usage guides
- **Production Ready**: Context managers, connection pooling, and proper resource cleanup
- **Tested**: 100+ test cases covering all functionality
- **AI Agent Friendly**: Clean interfaces designed for autonomous agent integration

## Installation

### From Source

```bash
cd net_agents
pip install -e .
```

### With Development Dependencies

```bash
cd net_agents
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from network_simulator_client import NetworkSimulatorClient

# Create client
client = NetworkSimulatorClient(base_url="http://localhost:8003")

# Check API health
health = client.health_check()
print(f"API Status: {health.status}")

# Get all nodes
nodes = client.get_nodes()
print(f"Found {len(nodes)} nodes")

# Clean up
client.close()
```

### Using Context Manager (Recommended)

```python
from network_simulator_client import NetworkSimulatorClient

with NetworkSimulatorClient(base_url="http://localhost:8003") as client:
    # Get database statistics
    stats = client.get_database_stats()
    print(f"Nodes: {stats.nodes}, Edges: {stats.edges}, Services: {stats.services}")

    # Filter nodes by vendor
    cisco_nodes = client.get_nodes(vendor="Cisco")
    print(f"Cisco nodes: {len(cisco_nodes)}")
# Client automatically closes when exiting context
```

## API Reference

### Client Initialization

```python
NetworkSimulatorClient(
    base_url="http://localhost:8003",  # API base URL
    timeout=30.0,                       # Request timeout in seconds
    max_retries=3,                      # Maximum retry attempts
    verify_ssl=True                     # Verify SSL certificates
)
```

### Node Management

```python
# Get all nodes (with optional filters)
nodes = client.get_nodes(
    vendor="Cisco",              # Filter by vendor
    min_total_capacity=100.0,    # Minimum total capacity (Gbps)
    max_total_capacity=200.0,    # Maximum total capacity (Gbps)
    min_free_capacity=50.0,      # Minimum free capacity (Gbps)
    latitude=40.7128,            # Geographic filter (requires all 3)
    longitude=-74.0060,
    max_distance_km=500.0
)

# Get specific node
node = client.get_node(node_uuid="550e8400-e29b-41d4-a716-446655440000")

# Search nodes by name (substring, case-insensitive)
nodes = client.search_nodes_by_name("NYC")

# Create new node
from network_simulator_client.models import NodeCreate

new_node = NodeCreate(
    name="NYC-Core-01",
    latitude=40.7128,
    longitude=-74.0060,
    vendor="Cisco",
    capacity_gbps=100.0
)
created_node = client.create_node(new_node)

# Update node
from network_simulator_client.models import NodeUpdate

update = NodeUpdate(capacity_gbps=200.0, vendor="Juniper")
updated_node = client.update_node(node_uuid, update)

# Delete node
client.delete_node(node_uuid)  # Raises ResourceConflictError if referenced
```

### Edge Management

```python
# Get all edges
edges = client.get_edges()

# Get specific edge
edge = client.get_edge(edge_uuid)

# Get edge by endpoint nodes
edge = client.get_edge_by_endpoints(node1_uuid, node2_uuid)

# Create new edge
from network_simulator_client.models import EdgeCreate

new_edge = EdgeCreate(
    node1_uuid="550e8400-e29b-41d4-a716-446655440000",
    node2_uuid="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    capacity_gbps=50.0
)
created_edge = client.create_edge(new_edge)

# Delete edge
client.delete_edge(edge_uuid)  # Raises ResourceConflictError if referenced
```

### Service Management

```python
# Get all services (with optional limit)
services = client.get_services(limit=100)

# Get specific service
service = client.get_service(service_uuid)

# Get services by source node
services = client.get_services_by_node(node_uuid)

# Get services traversing an edge
services = client.get_services_by_edge(edge_uuid)

# Create new service
from network_simulator_client.models import ServiceCreate

new_service = ServiceCreate(
    name="Service-NYC-BOS-001",
    source_node_uuid="550e8400-e29b-41d4-a716-446655440000",
    destination_node_uuid="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    demand_gbps=10.0,
    routing_stage="stage_a",
    path_node_uuids=["uuid1", "uuid2", "uuid3"],
    path_edge_uuids=["edge1", "edge2"],
    total_distance_km=347.5,
    service_timestamp="2024-01-15T12:00:00Z"
)
created_service = client.create_service(new_service)

# Delete service (frees capacity on edges)
client.delete_service(service_uuid)
```

### Routing

```python
# Compute optimal route using A* algorithm
route = client.compute_route(
    source_node_uuid="550e8400-e29b-41d4-a716-446655440000",
    destination_node_uuid="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    demand_gbps=10.0  # Optional, default: 5.0
)

print(f"Route found!")
print(f"  Distance: {route.total_distance_km:.2f} km")
print(f"  Hops: {route.hop_count}")
print(f"  Min Available Capacity: {route.min_available_capacity:.2f} Gbps")
print(f"  Computation Time: {route.computation_time_ms:.2f} ms")
print(f"  Path: {len(route.path_node_uuids)} nodes, {len(route.path_edge_uuids)} edges")

# Alternative: GET method
route = client.compute_route_get(source_uuid, dest_uuid, demand_gbps=10.0)
```

### Capacity & Analytics

```python
# Get database statistics
stats = client.get_database_stats()
print(f"Nodes: {stats.nodes}, Edges: {stats.edges}, Services: {stats.services}")

# Get capacity utilization summary (sorted by utilization %)
summary = client.get_capacity_summary()
for edge in summary[:10]:  # Top 10 most utilized
    print(f"Edge {edge.uuid}: {edge.utilization_pct:.1f}% utilized")
    print(f"  Capacity: {edge.capacity_gbps} Gbps")
    print(f"  Demand: {edge.total_demand_gbps} Gbps")
    print(f"  Services: {edge.service_count}")

# Get utilization for specific edge
utilization = client.get_edge_utilization(edge_uuid)

# Get capacity violations (oversubscribed edges)
violations = client.get_capacity_violations()
for violation in violations:
    print(f"Edge {violation.edge_uuid} is oversubscribed!")
    print(f"  Capacity: {violation.capacity_gbps} Gbps")
    print(f"  Demand: {violation.total_demand_gbps} Gbps")
    print(f"  Overage: {violation.overage} Gbps")
```

### Helper Methods

```python
# Get high utilization edges
high_util = client.get_high_utilization_edges(threshold_pct=80.0)

# Get node by exact name
node = client.get_node_by_name_exact("NYC-Core-01")

# Validate a path
validation = client.validate_path(
    path_node_uuids=["uuid1", "uuid2", "uuid3"],
    path_edge_uuids=["edge1", "edge2"],
    demand_gbps=10.0
)
if validation["valid"]:
    print(f"Path is valid!")
    print(f"  Distance: {validation['total_distance_km']} km")
    print(f"  Min Capacity: {validation['min_available_capacity']} Gbps")
else:
    print(f"Path is invalid:")
    for error in validation["errors"]:
        print(f"  - {error}")
```

## Error Handling

The SDK provides a comprehensive exception hierarchy for robust error handling:

```python
from network_simulator_client import (
    NetworkSimulatorClient,
    NodeNotFoundError,
    EdgeNotFoundError,
    ServiceNotFoundError,
    RouteNotFoundError,
    ValidationError,
    ResourceConflictError,
    APIConnectionError,
    APITimeoutError,
)

try:
    node = client.get_node("non-existent-uuid")
except NodeNotFoundError as e:
    print(f"Node not found: {e.message}")
    print(f"Status code: {e.status_code}")
except APIConnectionError:
    print("Failed to connect to API")
except APITimeoutError:
    print("Request timed out")
```

### Exception Hierarchy

```
NetworkSimulatorError (base)
├── APIConnectionError
├── APITimeoutError
├── ValidationError (400)
├── ResourceNotFoundError (404)
│   ├── NodeNotFoundError
│   ├── EdgeNotFoundError
│   └── ServiceNotFoundError
├── ResourceConflictError (409)
├── RouteNotFoundError (422)
├── CapacityViolationError
├── AuthenticationError (401)
├── AuthorizationError (403)
├── RateLimitError (429)
└── ServerError (5xx)
```

## Examples

The `examples/` directory contains comprehensive example scripts:

### Run Examples

```bash
# Basic CRUD operations
python examples/basic_usage.py

# Routing and pathfinding
python examples/routing_workflow.py

# Capacity monitoring and analytics
python examples/capacity_monitoring.py

# Service lifecycle management
python examples/service_lifecycle.py
```

### Example: Complete Workflow

```python
from network_simulator_client import NetworkSimulatorClient, ServiceCreate
from datetime import datetime

with NetworkSimulatorClient() as client:
    # 1. Find available nodes
    nodes = client.get_nodes(min_free_capacity=50.0)
    source = nodes[0]
    destination = nodes[-1]

    # 2. Compute optimal route
    route = client.compute_route(
        source_node_uuid=source.uuid,
        destination_node_uuid=destination.uuid,
        demand_gbps=10.0
    )

    print(f"Route: {route.hop_count} hops, {route.total_distance_km:.1f} km")

    # 3. Validate route capacity
    if route.min_available_capacity >= 10.0:
        # 4. Create service
        service = ServiceCreate(
            name=f"Service-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            source_node_uuid=source.uuid,
            destination_node_uuid=destination.uuid,
            demand_gbps=10.0,
            routing_stage="stage_a",
            path_node_uuids=route.path_node_uuids,
            path_edge_uuids=route.path_edge_uuids,
            total_distance_km=route.total_distance_km,
            service_timestamp=datetime.utcnow().isoformat() + "Z"
        )

        created = client.create_service(service)
        print(f"Created service: {created.uuid}")

        # 5. Monitor capacity impact
        for edge_uuid in created.path_edge_uuids:
            util = client.get_edge_utilization(edge_uuid)
            print(f"  Edge {edge_uuid[:8]}...: {util.utilization_pct:.1f}% utilized")
    else:
        print(f"Insufficient capacity: only {route.min_available_capacity:.1f} Gbps available")
```

## Testing

Run the test suite:

```bash
cd net_agents

# Run all tests
pytest

# Run with coverage
pytest --cov=network_simulator_client

# Run specific test file
pytest tests/test_nodes.py

# Run with verbose output
pytest -v
```

## AI Agent Integration

This SDK is designed for AI agent integration with:

- **Clean Interfaces**: Simple, intuitive method names
- **Type Safety**: Full type hints for IDE autocomplete
- **Error Context**: Detailed exceptions with actionable information
- **Idempotent Operations**: Safe to retry on failure
- **Resource Management**: Automatic cleanup via context managers

### Example: Simple AI Agent

```python
class NetworkAgent:
    def __init__(self, api_url: str):
        self.client = NetworkSimulatorClient(base_url=api_url)

    def find_best_route(self, source_name: str, dest_name: str, demand: float):
        """Find the best route between two nodes by name."""
        # Find nodes
        source = self.client.get_node_by_name_exact(source_name)
        dest = self.client.get_node_by_name_exact(dest_name)

        if not source or not dest:
            return None

        # Compute route
        try:
            route = self.client.compute_route(
                source_node_uuid=source.uuid,
                destination_node_uuid=dest.uuid,
                demand_gbps=demand
            )
            return {
                "success": True,
                "distance": route.total_distance_km,
                "hops": route.hop_count,
                "capacity": route.min_available_capacity
            }
        except RouteNotFoundError:
            return {"success": False, "reason": "No feasible route"}

    def monitor_network_health(self):
        """Check for network issues."""
        issues = []

        # Check for violations
        violations = self.client.get_capacity_violations()
        if violations:
            issues.append(f"{len(violations)} oversubscribed edges")

        # Check for high utilization
        high_util = self.client.get_high_utilization_edges(threshold_pct=85.0)
        if high_util:
            issues.append(f"{len(high_util)} edges at >85% utilization")

        return {
            "healthy": len(issues) == 0,
            "issues": issues
        }
```

## Data Models

All request and response models are Pydantic models with full validation:

- `NodeCreate`, `NodeUpdate`, `NodeResponse`
- `EdgeCreate`, `EdgeResponse`
- `ServiceCreate`, `ServiceResponse`
- `RouteRequest`, `RouteResponse`
- `DatabaseStatsResponse`
- `EdgeUtilizationResponse`
- `CapacityViolationResponse`
- `HealthResponse`

See `network_simulator_client/models.py` for complete model definitions.

## API Endpoint Coverage

| Category | Endpoints | Methods |
|----------|-----------|---------|
| Health & Status | `/health` | `health_check()` |
| Node Management | `/nodes`, `/nodes/{uuid}`, `/nodes/by-name/{name}` | `get_nodes()`, `get_node()`, `create_node()`, `update_node()`, `delete_node()`, `search_nodes_by_name()` |
| Edge Management | `/edges`, `/edges/{uuid}`, `/edges/by-endpoints` | `get_edges()`, `get_edge()`, `create_edge()`, `delete_edge()`, `get_edge_by_endpoints()` |
| Service Management | `/services`, `/services/{uuid}`, `/services/by-node/{uuid}`, `/services/by-edge/{uuid}` | `get_services()`, `get_service()`, `create_service()`, `delete_service()`, `get_services_by_node()`, `get_services_by_edge()` |
| Routing | `/routing/astar` | `compute_route()`, `compute_route_get()` |
| Capacity & Analytics | `/capacity/summary`, `/capacity/edge/{uuid}`, `/capacity/violations`, `/analytics/stats` | `get_capacity_summary()`, `get_edge_utilization()`, `get_capacity_violations()`, `get_database_stats()` |

## Requirements

- Python 3.8+
- httpx >= 0.25.0
- pydantic >= 2.0.0

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting (optional)
ruff check network_simulator_client/

# Format code (optional)
black network_simulator_client/
```

## License

This SDK is part of the AutoCon project.

## Support

For issues or questions:
1. Check the examples in `examples/`
2. Review the API documentation
3. Check the test suite in `tests/` for usage patterns

## Version

Current version: 0.1.0

## Changelog

### 0.1.0 (Initial Release)
- Complete API coverage for all endpoints
- Comprehensive error handling
- Full test suite (100+ tests)
- Example scripts for all major workflows
- Type hints and Pydantic validation
- Context manager support
- Helper methods for common operations
