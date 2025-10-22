# Network Simulator Quick Reference

A practical guide to the network topology and SDK for building AI agents.

---

## Network Overview

### Topology
- **48 Network Nodes** distributed across eastern United States
- **~200 Edges** (bidirectional connections between nodes)
- **~100 Services** already provisioned
- Geographic routing with real distances

### Node Characteristics
- **Location**: Real city coordinates (latitude/longitude)
- **Capacity**: 200-5000 Gbps per node
- **Vendors**: Multiple vendors (Suomi Networks, Agave Networks, Toscana Systems, etc.)
- **Free Capacity**: Available bandwidth for new services

### Edge (Connection) Characteristics
- **Capacity**: Varies per edge (typically 50-100 Gbps)
- **Utilization**: Currently ~6% average
- **Bidirectional**: Can route traffic both ways
- **Geographic Distance**: Based on actual node locations

### Service Characteristics
- **Demand**: Bandwidth requirement (typically 5-10 Gbps)
- **Path**: Ordered list of nodes traversed
- **Hops**: Number of edges in the path
- **Distance**: Total geographic distance in km

---

## SDK Quick Reference

### Initialize Client

```python
from network_simulator_client import NetworkSimulatorClient

# With context manager (recommended)
with NetworkSimulatorClient(base_url="http://localhost:8003") as client:
    # Your code here
    pass

# Or manual management
client = NetworkSimulatorClient(base_url="http://localhost:8003")
# ... use client ...
client.close()
```

---

## Common Operations

### 1. Get Network Overview

```python
# Database statistics
stats = client.get_database_stats()
print(f"Nodes: {stats.nodes}, Edges: {stats.edges}, Services: {stats.services}")
```

### 2. Working with Nodes

```python
# Get all nodes
nodes = client.get_nodes()

# Get specific node
node = client.get_node(node_uuid="uuid-string")

# Search by name (case-insensitive substring)
matching_nodes = client.search_nodes_by_name("Albany")

# Filter by vendor
cisco_nodes = client.get_nodes(vendor="Suomi Networks")

# Filter by capacity
high_capacity = client.get_nodes(
    min_total_capacity=1000.0,
    max_total_capacity=3000.0
)

# Filter by available capacity
available_nodes = client.get_nodes(min_free_capacity=100.0)

# Geographic filter (within radius)
nearby = client.get_nodes(
    latitude=40.7128,   # NYC
    longitude=-74.0060,
    max_distance_km=500.0
)

# Get node by exact name
node = client.get_node_by_name_exact("Albany-NY")
```

**Node Response Fields:**
```python
node.uuid                 # Unique identifier
node.name                 # Human-readable name
node.latitude             # Geographic coordinate
node.longitude            # Geographic coordinate
node.vendor               # Equipment vendor
node.capacity_gbps        # Total capacity
node.free_capacity_gbps   # Available capacity
node.created_at           # Timestamp
node.updated_at           # Timestamp
```

### 3. Working with Edges

```python
# Get all edges
edges = client.get_edges()

# Get specific edge
edge = client.get_edge(edge_uuid="uuid-string")

# Find edge between two nodes
edge = client.get_edge_by_endpoints(node1_uuid, node2_uuid)
```

**Edge Response Fields:**
```python
edge.uuid          # Unique identifier
edge.node1_uuid    # First endpoint
edge.node2_uuid    # Second endpoint
edge.capacity_gbps # Edge capacity
edge.created_at    # Timestamp
edge.updated_at    # Timestamp
```

### 4. Computing Routes

```python
# Compute route with A* algorithm
route = client.compute_route(
    source_node_uuid=source.uuid,
    destination_node_uuid=dest.uuid,
    demand_gbps=10.0  # Optional, default: 5.0
)

# Access route details
print(f"Distance: {route.total_distance_km} km")
print(f"Hops: {route.hop_count}")
print(f"Min capacity: {route.min_available_capacity} Gbps")
print(f"Computation time: {route.computation_time_ms} ms")
print(f"Path nodes: {route.path_node_uuids}")
print(f"Path edges: {route.path_edge_uuids}")
```

**Route Response Fields:**
```python
route.source_node_uuid          # Start node
route.destination_node_uuid     # End node
route.path_node_uuids           # Ordered list of nodes
route.path_edge_uuids           # Ordered list of edges
route.total_distance_km         # Geographic distance
route.hop_count                 # Number of edges
route.min_available_capacity    # Bottleneck capacity
route.computation_time_ms       # Algorithm runtime
route.demand_gbps               # Requested bandwidth
```

### 5. Managing Services

```python
# Get all services
services = client.get_services(limit=100)

# Get specific service
service = client.get_service(service_uuid="uuid-string")

# Get services by source node
node_services = client.get_services_by_node(node_uuid)

# Get services traversing an edge
edge_services = client.get_services_by_edge(edge_uuid)

# Create new service
from network_simulator_client.models import ServiceCreate
from datetime import datetime

service_data = ServiceCreate(
    name="My-Service",
    source_node_uuid=source.uuid,
    destination_node_uuid=dest.uuid,
    demand_gbps=10.0,
    routing_stage="stage_a",
    path_node_uuids=route.path_node_uuids,
    path_edge_uuids=route.path_edge_uuids,
    total_distance_km=route.total_distance_km,
    service_timestamp=datetime.utcnow().isoformat() + "Z"
)
created = client.create_service(service_data)

# Delete service (frees capacity)
client.delete_service(service_uuid)
```

**Service Response Fields:**
```python
service.uuid                 # Unique identifier
service.name                 # Service name
service.source_node_uuid     # Start node
service.destination_node_uuid # End node
service.demand_gbps          # Bandwidth requirement
service.hop_count            # Number of hops
service.total_distance_km    # Path distance
service.routing_stage        # "stage_a" or "stage_b"
service.path_node_uuids      # Ordered node list
service.path_edge_uuids      # Ordered edge list
service.created_at           # Timestamp
```

### 6. Capacity Monitoring

```python
# Get utilization summary for all edges
summary = client.get_capacity_summary()
for edge_util in summary[:10]:  # Top 10 most utilized
    print(f"Edge {edge_util.uuid[:8]}: {edge_util.utilization_pct}%")

# Get specific edge utilization
util = client.get_edge_utilization(edge_uuid)
print(f"Capacity: {util.capacity_gbps} Gbps")
print(f"Demand: {util.total_demand_gbps} Gbps")
print(f"Services: {util.service_count}")
print(f"Utilization: {util.utilization_pct}%")

# Check for capacity violations
violations = client.get_capacity_violations()
for v in violations:
    print(f"Edge {v.edge_uuid} oversubscribed by {v.overage} Gbps")

# Get high-utilization edges
high_util = client.get_high_utilization_edges(threshold_pct=80.0)
```

### 7. Path Validation

```python
# Validate path before creating service
validation = client.validate_path(
    path_node_uuids=["uuid1", "uuid2", "uuid3"],
    path_edge_uuids=["edge1", "edge2"],
    demand_gbps=10.0
)

if validation["valid"]:
    print(f"Path is valid!")
    print(f"  Distance: {validation['total_distance_km']} km")
    print(f"  Min capacity: {validation['min_available_capacity']} Gbps")
else:
    print("Path is invalid:")
    for error in validation["errors"]:
        print(f"  - {error}")
```

---

## Common Patterns for AI Agents

### Pattern 1: Find Best Node for Service

```python
def find_best_source_node(client, min_capacity=50.0):
    """Find node with most available capacity."""
    nodes = client.get_nodes(min_free_capacity=min_capacity)
    if not nodes:
        return None

    # Sort by free capacity
    best = max(nodes, key=lambda n: n.free_capacity_gbps)
    return best
```

### Pattern 2: Check Route Feasibility

```python
def can_route_service(client, source_uuid, dest_uuid, demand_gbps):
    """Check if route with capacity exists."""
    try:
        route = client.compute_route(source_uuid, dest_uuid, demand_gbps)
        return route.min_available_capacity >= demand_gbps
    except RouteNotFoundError:
        return False
```

### Pattern 3: Find Congested Areas

```python
def find_congestion(client, threshold=80.0):
    """Find edges approaching capacity."""
    high_util = client.get_high_utilization_edges(threshold_pct=threshold)
    violations = client.get_capacity_violations()

    return {
        "high_utilization": len(high_util),
        "violations": len(violations),
        "critical_edges": [e.uuid for e in high_util] + [v.edge_uuid for v in violations]
    }
```

### Pattern 4: Provision Service Safely

```python
def provision_service_with_checks(client, source_uuid, dest_uuid, demand_gbps):
    """Provision service with pre-checks."""
    # 1. Compute route
    try:
        route = client.compute_route(source_uuid, dest_uuid, demand_gbps)
    except RouteNotFoundError:
        return {"success": False, "error": "No feasible route"}

    # 2. Validate capacity
    if route.min_available_capacity < demand_gbps:
        return {"success": False, "error": "Insufficient capacity"}

    # 3. Validate path
    validation = client.validate_path(
        route.path_node_uuids,
        route.path_edge_uuids,
        demand_gbps
    )
    if not validation["valid"]:
        return {"success": False, "error": validation["errors"]}

    # 4. Create service
    from network_simulator_client.models import ServiceCreate
    from datetime import datetime

    service = ServiceCreate(
        name=f"Service-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        source_node_uuid=source_uuid,
        destination_node_uuid=dest_uuid,
        demand_gbps=demand_gbps,
        routing_stage="stage_a",
        path_node_uuids=route.path_node_uuids,
        path_edge_uuids=route.path_edge_uuids,
        total_distance_km=route.total_distance_km,
        service_timestamp=datetime.utcnow().isoformat() + "Z"
    )

    created = client.create_service(service)
    return {"success": True, "service_uuid": created.uuid}
```

---

## Error Handling

### Exception Hierarchy

```python
from network_simulator_client import (
    NetworkSimulatorError,        # Base exception
    APIConnectionError,            # Can't connect to API
    APITimeoutError,               # Request timed out
    NodeNotFoundError,             # Node doesn't exist
    EdgeNotFoundError,             # Edge doesn't exist
    ServiceNotFoundError,          # Service doesn't exist
    RouteNotFoundError,            # No feasible route
    ValidationError,               # Invalid input
    ResourceConflictError,         # Can't delete (referenced)
)
```

### Handling Common Errors

```python
try:
    route = client.compute_route(source, dest, demand_gbps=100.0)
except RouteNotFoundError:
    print("No route with sufficient capacity")
except NodeNotFoundError:
    print("One or both nodes don't exist")
except APITimeoutError:
    print("Request timed out - API may be slow")
except APIConnectionError:
    print("Can't connect - is the simulator running?")
```

---

## Performance Tips

1. **Use context managers** - Automatic connection cleanup
2. **Batch operations** - Get all nodes once, filter in memory
3. **Cache node lookups** - UUIDs don't change during execution
4. **Check capacity first** - Before computing expensive routes
5. **Validate before provisioning** - Catch errors early

---

## Network Statistics (Typical)

- **Nodes**: 48
- **Edges**: 200
- **Services**: 100
- **Average node capacity**: 1,625 Gbps
- **Average edge capacity**: 70 Gbps
- **Average utilization**: 6.2%
- **Average path hops**: 3-4 hops
- **Network health**: Excellent (no violations)

---

## Useful Code Snippets

### Get Network Summary

```python
def print_network_summary(client):
    stats = client.get_database_stats()
    violations = client.get_capacity_violations()
    high_util = client.get_high_utilization_edges(80.0)

    print(f"Network: {stats.nodes}N / {stats.edges}E / {stats.services}S")
    print(f"Violations: {len(violations)}")
    print(f"High utilization (≥80%): {len(high_util)}")
```

### Find Node by City

```python
def find_node_by_city(client, city_name):
    """Find node by partial city name match."""
    results = client.search_nodes_by_name(city_name)
    if not results:
        return None
    # Return first match
    return results[0]
```

### Calculate Path Distance

```python
from network_simulator_client.utils import haversine_distance

def calculate_direct_distance(client, node1_uuid, node2_uuid):
    """Calculate straight-line distance between nodes."""
    node1 = client.get_node(node1_uuid)
    node2 = client.get_node(node2_uuid)

    return haversine_distance(
        node1.latitude, node1.longitude,
        node2.latitude, node2.longitude
    )
```

---

## For More Information

- **Full SDK Documentation**: `../README.md`
- **API Interactive Docs**: http://localhost:8003/docs
- **Test Report**: `../TEST_REPORT.md`
- **Example Scripts**: `../examples/`

---

**Ready to build agents?** → Start with [EXERCISE_GUIDE.md](EXERCISE_GUIDE.md)
