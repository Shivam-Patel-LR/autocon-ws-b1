# Network Simulator API Usage Guide

Guide to using the Network Simulator REST API.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Documentation](#api-documentation)
4. [Common Workflows](#common-workflows)
5. [Endpoint Reference](#endpoint-reference)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Advanced Usage](#advanced-usage)

---

## Getting Started

### Starting the API

**Using Docker (Recommended):**
```bash
cd network_simulator
docker compose up --build
```

**Using Python Directly:**
```bash
cd network_simulator
uv run python run_api.py
# or: python -m uvicorn src.api:app --host 0.0.0.0 --port 8003
```

### Accessing the API

Once running, the API is available at:
- **Base URL**: http://localhost:8003
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **OpenAPI JSON**: http://localhost:8003/openapi.json

### Quick Health Check

```bash
curl http://localhost:8003/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-15T15:41:56.883504Z"
}
```

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## API Documentation

### Interactive Swagger UI

Visit **http://localhost:8003/docs** for interactive API documentation where you can:
- Browse all available endpoints
- View request/response schemas with examples
- Test endpoints directly from your browser
- Generate curl commands
- Download OpenAPI specification

### ReDoc Documentation

Visit **http://localhost:8003/redoc** for a clean, scrollable API reference with:
- Comprehensive endpoint descriptions
- Request/response examples
- Schema definitions
- Search functionality

---

## Common Workflows

### 1. Exploring the Network

```bash
# Get database statistics
curl http://localhost:8003/analytics/stats

# List all nodes
curl http://localhost:8003/nodes

# Filter nodes by vendor
curl "http://localhost:8003/nodes?vendor=TeleConnect"

# Filter nodes by minimum capacity
curl "http://localhost:8003/nodes?min_capacity=4000"

# List all edges
curl http://localhost:8003/edges
```

### 2. Getting Specific Resources

```bash
# Get a node by UUID
curl http://localhost:8003/nodes/f9581593-4f1f-4da5-83ba-73aacd2cc101

# Get a node by name
curl http://localhost:8003/nodes/by-name/NYC-Manhattan

# Get an edge by UUID
curl http://localhost:8003/edges/0c929850-79fc-4acd-a69d-163dc318353a

# Get an edge by endpoints (node UUIDs)
curl "http://localhost:8003/edges/by-endpoints/?node1_uuid=UUID1&node2_uuid=UUID2"
```

### 3. Creating New Resources

**Create a Node:**
```bash
curl -X POST http://localhost:8003/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detroit-Downtown",
    "latitude": 42.3314,
    "longitude": -83.0458,
    "vendor": "TeleConnect",
    "capacity_gbps": 3500.0
  }'
```

**Create an Edge:**
```bash
curl -X POST http://localhost:8003/edges \
  -H "Content-Type: application/json" \
  -d '{
    "node1_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
    "node2_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
    "capacity_gbps": 150.0
  }'
```

### 4. Updating Resources

```bash
curl -X PUT http://localhost:8003/nodes/f9581593-4f1f-4da5-83ba-73aacd2cc101 \
  -H "Content-Type: application/json" \
  -d '{
    "capacity_gbps": 6000.0,
    "vendor": "NewVendor"
  }'
```

### 5. Deleting Resources

```bash
# Delete a node (only if not referenced by edges/services)
curl -X DELETE http://localhost:8003/nodes/NODE_UUID

# Delete an edge (only if not referenced by services)
curl -X DELETE http://localhost:8003/edges/EDGE_UUID
```

### 6. Analyzing Capacity

```bash
# Get capacity utilization for all edges (sorted by utilization %)
curl http://localhost:8003/capacity/summary

# Get capacity for a specific edge
curl http://localhost:8003/capacity/edge/EDGE_UUID

# Find capacity violations (edges exceeding capacity)
curl http://localhost:8003/capacity/violations
```

---

## Endpoint Reference

### Health Endpoints

#### GET /health
**Description:** Check API and database health status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-15T15:41:56.883504Z"
}
```

---

### Node Endpoints

#### GET /nodes
**Description:** List all network nodes

**Query Parameters:**
- `vendor` (optional): Filter by vendor name
- `min_capacity` (optional): Filter by minimum capacity in Gbps

**Example:**
```bash
curl "http://localhost:8003/nodes?vendor=TeleConnect&min_capacity=4000"
```

**Response:**
```json
[
  {
    "uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
    "name": "NYC-Manhattan",
    "latitude": 40.7589,
    "longitude": -73.9851,
    "vendor": "TeleConnect",
    "capacity_gbps": 5000.0,
    "created_at": "2025-10-15T10:30:00Z",
    "updated_at": "2025-10-15T10:30:00Z"
  }
]
```

#### GET /nodes/{uuid}
**Description:** Get a specific node by UUID

**Path Parameters:**
- `uuid`: Node UUID

**Response Codes:**
- `200`: Success
- `404`: Node not found

#### GET /nodes/by-name/{name}
**Description:** Get a specific node by name

**Path Parameters:**
- `name`: Node name (e.g., "NYC-Manhattan")

**Response Codes:**
- `200`: Success
- `404`: Node not found

#### POST /nodes
**Description:** Create a new node

**Request Body:**
```json
{
  "name": "Detroit-Downtown",
  "latitude": 42.3314,
  "longitude": -83.0458,
  "vendor": "TeleConnect",
  "capacity_gbps": 3500.0
}
```

**Response Codes:**
- `201`: Created successfully
- `400`: Invalid input or duplicate name

#### PUT /nodes/{uuid}
**Description:** Update an existing node

**Path Parameters:**
- `uuid`: Node UUID

**Request Body:** (all fields optional)
```json
{
  "capacity_gbps": 6000.0,
  "vendor": "NewVendor"
}
```

**Response Codes:**
- `200`: Updated successfully
- `404`: Node not found

#### DELETE /nodes/{uuid}
**Description:** Delete a node

**Response Codes:**
- `204`: Deleted successfully
- `404`: Node not found
- `409`: Node is referenced by edges or services

---

### Edge Endpoints

#### GET /edges
**Description:** List all network edges

**Response:**
```json
[
  {
    "uuid": "0c929850-79fc-4acd-a69d-163dc318353a",
    "node1_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
    "node2_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
    "capacity_gbps": 100.0,
    "created_at": "2025-10-15T10:30:00Z",
    "updated_at": "2025-10-15T10:30:00Z"
  }
]
```

#### GET /edges/{uuid}
**Description:** Get a specific edge by UUID

**Response Codes:**
- `200`: Success
- `404`: Edge not found

#### GET /edges/by-endpoints/
**Description:** Get an edge by its endpoint node UUIDs

**Query Parameters:**
- `node1_uuid`: First node UUID
- `node2_uuid`: Second node UUID

**Example:**
```bash
curl "http://localhost:8003/edges/by-endpoints/?node1_uuid=UUID1&node2_uuid=UUID2"
```

**Response Codes:**
- `200`: Success
- `404`: Edge not found

#### POST /edges
**Description:** Create a new edge between two nodes

**Request Body:**
```json
{
  "node1_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
  "node2_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
  "capacity_gbps": 150.0
}
```

**Response Codes:**
- `201`: Created successfully
- `400`: Invalid input or duplicate edge
- `404`: One or both nodes not found

#### DELETE /edges/{uuid}
**Description:** Delete an edge

**Response Codes:**
- `204`: Deleted successfully
- `404`: Edge not found
- `409`: Edge is referenced by services

---

### Analytics Endpoints

#### GET /analytics/stats
**Description:** Get database statistics

**Response:**
```json
{
  "nodes": 48,
  "edges": 200,
  "services": 100
}
```

#### GET /capacity/summary
**Description:** Get capacity utilization for all edges (sorted by utilization %)

**Response:**
```json
[
  {
    "uuid": "0c929850-79fc-4acd-a69d-163dc318353a",
    "capacity_gbps": 100.0,
    "total_demand_gbps": 45.0,
    "service_count": 9,
    "utilization_pct": 45.0
  }
]
```

#### GET /capacity/edge/{uuid}
**Description:** Get capacity utilization for a specific edge

**Response Codes:**
- `200`: Success
- `404`: Edge not found

#### GET /capacity/violations
**Description:** Get all edges where demand exceeds capacity

**Response:**
```json
[
  {
    "edge_uuid": "0c929850-79fc-4acd-a69d-163dc318353a",
    "capacity_gbps": 100.0,
    "total_demand_gbps": 120.0,
    "overage": 20.0
  }
]
```

---

## Error Handling

### Error Response Format

All errors return a JSON response with a `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid input or validation error
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource cannot be deleted due to references
- `503 Service Unavailable`: Database not available

### Example Error Responses

**404 Not Found:**
```json
{
  "detail": "Node with UUID f9581593-4f1f-4da5-83ba-73aacd2cc101 not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Node with name 'NYC-Manhattan' already exists"
}
```

**409 Conflict:**
```json
{
  "detail": "Cannot delete node: It may be referenced by edges or services."
}
```

---

## Best Practices

### 1. Always Check Health First

Before making requests, verify the API is healthy:
```bash
curl http://localhost:8003/health
```

### 2. Use Filters to Reduce Response Size

Instead of fetching all nodes and filtering client-side:
```bash
# Good: Filter server-side
curl "http://localhost:8003/nodes?vendor=TeleConnect"

# Less efficient: Fetch all and filter client-side
curl http://localhost:8003/nodes | jq '.[] | select(.vendor=="TeleConnect")'
```

### 3. Handle Errors Gracefully

Always check HTTP status codes and parse error messages:
```bash
response=$(curl -s -w "\n%{http_code}" http://localhost:8003/nodes/INVALID_UUID)
status=$(echo "$response" | tail -1)
body=$(echo "$response" | head -1)

if [ "$status" -eq 404 ]; then
  echo "Node not found: $body"
fi
```

### 4. Use UUIDs for Reliable References

UUIDs are immutable and globally unique. Names can change.
```bash
# Good: Reference by UUID
curl http://localhost:8003/nodes/f9581593-4f1f-4da5-83ba-73aacd2cc101

# Okay but less reliable: Reference by name
curl http://localhost:8003/nodes/by-name/NYC-Manhattan
```

### 5. Monitor Capacity Utilization

Regularly check for capacity violations:
```bash
curl http://localhost:8003/capacity/violations
```

---

## Advanced Usage

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8003"

# Get all nodes
response = requests.get(f"{BASE_URL}/nodes")
nodes = response.json()

# Create a node
new_node = {
    "name": "Detroit-Downtown",
    "latitude": 42.3314,
    "longitude": -83.0458,
    "vendor": "TeleConnect",
    "capacity_gbps": 3500.0
}
response = requests.post(f"{BASE_URL}/nodes", json=new_node)
if response.status_code == 201:
    created_node = response.json()
    print(f"Created node: {created_node['uuid']}")
else:
    print(f"Error: {response.json()['detail']}")

# Get capacity summary
response = requests.get(f"{BASE_URL}/capacity/summary")
utilizations = response.json()
for util in utilizations:
    if util['utilization_pct'] > 80:
        print(f"Warning: Edge {util['uuid']} is {util['utilization_pct']:.1f}% utilized")
```

### Batch Operations

```bash
# Get all nodes and extract UUIDs
node_uuids=$(curl -s http://localhost:8003/nodes | jq -r '.[].uuid')

# Query each node
for uuid in $node_uuids; do
  curl -s http://localhost:8003/nodes/$uuid | jq '.name, .capacity_gbps'
done
```

### Monitoring Script

```bash
#!/bin/bash
# monitor.sh - Monitor API health and capacity

while true; do
  # Check health
  health=$(curl -s http://localhost:8003/health | jq -r '.status')
  echo "[$(date)] Health: $health"

  # Check for violations
  violations=$(curl -s http://localhost:8003/capacity/violations)
  count=$(echo "$violations" | jq 'length')
  echo "[$(date)] Capacity violations: $count"

  if [ "$count" -gt 0 ]; then
    echo "$violations" | jq '.'
  fi

  sleep 60
done
```

### Data Export

```bash
# Export all nodes to JSON
curl http://localhost:8003/nodes > nodes_export.json

# Export all edges to JSON
curl http://localhost:8003/edges > edges_export.json

# Export capacity summary to CSV
curl -s http://localhost:8003/capacity/summary | \
  jq -r '.[] | [.uuid, .capacity_gbps, .total_demand_gbps, .utilization_pct] | @csv' > capacity.csv
```

---

## Support & Resources

- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc
- Test Suite: Run `pytest tests/test_api.py -v` to see 41 API tests

---

## Quick Reference Card

```
Base URL: http://localhost:8003

HEALTH
  GET  /health                         Check API health

NODES
  GET    /nodes                         List all nodes
  GET    /nodes/{uuid}                  Get node by UUID
  GET    /nodes/by-name/{name}          Get node by name
  POST   /nodes                         Create node
  PUT    /nodes/{uuid}                  Update node
  DELETE /nodes/{uuid}                  Delete node

EDGES
  GET    /edges                         List all edges
  GET    /edges/{uuid}                  Get edge by UUID
  GET    /edges/by-endpoints/           Get edge by nodes
  POST   /edges                         Create edge
  DELETE /edges/{uuid}                  Delete edge

ANALYTICS
  GET  /analytics/stats                 Database statistics
  GET  /capacity/summary                All edge utilizations
  GET  /capacity/edge/{uuid}            Edge utilization
  GET  /capacity/violations             Capacity violations
```

---

*Last Updated: October 2025*
