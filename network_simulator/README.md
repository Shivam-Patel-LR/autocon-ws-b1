# Network Simulator

A network topology simulator for teaching demonstrations, running in Docker.

## Overview

This network simulator models network elements (NEs) distributed across the eastern United States and creates realistic network topologies with capacity-constrained connections. Each network element represents an abstracted node that handles routing, switching, and multiplexing. The simulator provides geographic visualizations of both the nodes and their interconnections.

## Features

### Network Elements
- **48 Network Elements** distributed across eastern US (east of Mississippi River)
- Major metro hubs with high capacity (2000-5000 Gbps)
- Smaller city nodes with moderate capacity (200-500 Gbps)
- Multiple vendor simulation (5 vendors)
- Total network capacity: 78,000 Gbps

### Connection Building
- **Three-Phase Algorithm** for creating realistic network topologies:
  - **Phase I**: Capacity-aware spanning tree for guaranteed connectivity
  - **Phase II**: Greedy augmentation toward hub-and-spoke structure
  - **Phase III**: Local spokes for non-hub nodes
- **Capacity Constraints**: All connections respect node capacity limits
- **Configurable Parameters**: gamma (capacity importance), beta (distance importance), eta (weight fraction)
- **Graph Verification**: Automatic validation of connectedness and capacity constraints
- Typically generates ~200 connections between nodes
- Average node degree: ~8 connections per node

### Visualizations
- **Network Map**: Geographic visualization using matplotlib and geopandas
- **Capacity Distribution**: Dual histograms showing node capacities and connection weights
- **Connection Map**: Network topology showing all connections with weight-based coloring
- Color-coded displays with continuous color gradients (log scale)
- US state boundaries with ocean background

### Data Export
- **Adjacency Matrix**: CSV export of full network topology
- Connection weights representing allocated capacity (Gbps)

## Quick Start

### Using Docker Compose (Recommended)

The container now runs a **FastAPI REST API** by default, exposing the network simulator data via HTTP endpoints.

```bash
# Build and run the API server
cd network_simulator
docker compose up --build

# The API will be available at:
# - Swagger UI: http://localhost:8003/docs
# - ReDoc: http://localhost:8003/redoc
# - Health Check: http://localhost:8003/health
```

To run data generation instead of the API:
```bash
docker compose run network-simulator python src/container_init.py
```

### Using Docker Directly

```bash
# Build the image
cd network_simulator
docker build -t network-simulator .

# Run the container
docker run -v $(pwd)/output:/app/output network-simulator
```

### Running Locally (without Docker)

```bash
cd network_simulator

# Install dependencies
pip install -r requirements.txt

# Run the simulator
python src/main.py
```

## Output

The simulator generates the following files:

### Visualizations (in `output/` directory)

1. **network_map.png** - Geographic map showing:
   - Network element locations on US eastern states map
   - Color-coded by capacity (green gradient)
   - Node sizes proportional to capacity
   - Network statistics overlay

2. **capacity_distribution.png** - Statistical charts showing:
   - Histogram of node capacity distribution
   - Histogram of connection weight distribution with statistics (mean, median, range)

3. **network_connections_map.png** - Connection topology showing:
   - All node-to-node connections overlaid on geographic map
   - Connection lines colored by weight (cool colormap: cyan/blue=low, magenta/purple=high)
   - Node capacity visualization with green gradient
   - Network statistics (nodes, connections, avg weight, total allocated capacity)

### Data Files (in `data/` directory)

4. **adjacency_matrix.csv** - Full network topology:
   - Square matrix with node names as rows/columns
   - Values represent connection weights in Gbps
   - Zero values indicate no direct connection
   - Useful for graph analysis and routing algorithms

## Data Structure

### Network Elements CSV

Located at `data/network_elements.csv` with the following columns:

- `name`: Network element identifier (e.g., "NYC-Manhattan")
- `lat`: Latitude coordinate
- `long`: Longitude coordinate
- `vendor`: Vendor/manufacturer name
- `capacity_gbps`: Total switching capacity in Gbps

## Architecture

```
network_simulator/
├── data/
│   ├── network.db              # SQLite database (primary storage)
│   ├── network_elements.csv    # Network element configurations
│   └── adjacency_matrix.csv    # Network topology matrix
├── src/
│   ├── api/                    # REST API module
│   │   ├── api.py              # FastAPI application
│   │   └── api_models.py       # Pydantic models
│   ├── core/                   # Core simulation
│   │   ├── network_simulator.py
│   │   ├── network_element.py
│   │   ├── connection_builder.py
│   │   └── config_loader.py
│   ├── database/               # Database layer
│   │   ├── database_manager.py
│   │   ├── database_verifier_inline.py
│   │   ├── db_to_dataframe.py
│   │   └── json_exporter.py
│   ├── services/               # Service generation
│   │   ├── generate_services_db.py
│   │   ├── dijkstra_router.py
│   │   ├── edge_cover.py
│   │   └── service.py
│   ├── visualization/          # Visualization
│   │   └── visualizer.py
│   ├── utilities/              # Utilities
│   │   ├── uuid_registry.py
│   │   └── dummy_network_generator.py
│   ├── main.py                 # Simulator entry point
│   └── container_init.py       # Container initialization
├── tests/
│   └── test_api.py             # API endpoint tests (41 tests)
├── scripts/                    # Utility scripts
│   ├── verify_database.py
│   ├── test_database.py
│   ├── clear_services.py
│   └── demo_database_queries.py
├── migrations/                 # Database migrations
│   ├── 001_initial_schema.sql
│   └── export_to_json.py
├── output/                     # Generated visualizations
├── run_api.py                  # API server runner
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Docker Compose config
└── requirements.txt            # Python dependencies
```

## Algorithm Details

### Three-Phase Connection Building

The simulator uses a sophisticated three-phase algorithm to create realistic network topologies:

**Phase I: Spanning Tree (Connectivity Guarantee)**
- Orders nodes by capacity (descending)
- Connects each node to its best parent based on preference score: S(u,v) = (Cu × Cv)^γ / d(u,v)^β
- Creates n-1 edges ensuring full graph connectivity
- Edge weight = η × min(Ru, Rv) where R is residual capacity

**Phase II: Greedy Augmentation (Hub-and-Spoke Formation)**
- Iteratively selects node pairs with highest preference scores
- Adds edges until target count reached or capacity exhausted
- Edge weight scales with normalized preference score: α(S) = 1/4 + S/4
- Naturally forms hub-and-spoke topology with high-capacity nodes as hubs

**Phase III: Local Spokes (Optional)**
- Non-hub nodes (bottom 75% by capacity) get additional connections
- Up to 2 additional connections to higher-capacity neighbors
- Only if target edge count not yet reached

**Graph Verification**
- BFS traversal confirms full connectivity
- Validates that no node exceeds capacity constraints
- Raises exception if verification fails

### Configurable Parameters

- **gamma (γ)**: Capacity importance (default: 1.5, typical: 1-2)
- **beta (β)**: Distance importance (default: 2.0, typical: 1-3)
- **eta (η)**: Weight fraction for Phase I (default: 0.4, must be in (0, 0.5])
- **target_edges**: Target connection count (default: 200, typical: 200-300)
- **noise_factor**: Random variation (default: 0.01)
- **random_seed**: Reproducibility seed (default: 42)

## Service Generation

The simulator generates network services that route through the topology using a capacity-constrained two-stage algorithm. Services are generated during container initialization and stored in the SQLite database.

### Usage

Service generation happens automatically during container initialization. To customize:

```bash
# Generate with custom service count
docker compose run -e NUM_SERVICES=200 network-simulator python src/container_init.py

# Skip service generation
docker compose run -e GENERATE_SERVICES=false network-simulator python src/container_init.py
```

### Algorithm Overview

The service routing uses a two-stage algorithm that guarantees endpoint coverage while respecting capacity constraints:

**Stage A: Guaranteed Endpoint Coverage**
- Computes minimum edge cover to ensure every node is an endpoint
- Uses maximum matching algorithm to minimize edge cover size
- Routes one-edge (single-hop) services on edges in the cover
- Guarantees all 48 nodes are covered as service endpoints

**Stage B: Randomized Dijkstra Routing**
- Routes additional services using capacity-aware Dijkstra
- Cost function: cost(e) = (r_e/D)^(-p) + noise
  - Favors edges with higher residual capacity
  - Random noise breaks ties for path diversity
- Endpoint sampling weighted by residual capacity
- Creates multi-hop paths through the network

### Configuration Parameters

Edit `config.json` under the `service_routing` section:

- **demand_gbps**: Bandwidth demand per service (default: 5.0 Gbps)
- **target_services**: Target number of services to generate (default: 100)
- **p_exponent**: Cost function exponent (default: 1.5)
  - Higher values → stronger preference for high-capacity edges
- **rho_exponent**: Endpoint sampling exponent (default: 1.0)
  - Higher values → more services on high-capacity hubs
- **noise_delta**: Tie-breaking noise range (default: 0.01)
- **random_seed**: For reproducible results (default: 42)
- **enable_stage_a**: Enable Stage A edge cover (default: true)

### Output Format

Services are exported to `data/services.json`:

```json
{
  "metadata": {
    "total_services": 100,
    "demand_per_service_gbps": 5.0,
    "stage_a_services": 24,
    "stage_b_services": 76,
    "generation_timestamp": "2025-10-14T18:14:22.155350Z"
  },
  "services": [
    {
      "service_id": "SVC-001",
      "name": "Service Flint-MI to Lansing-MI",
      "source": "Flint-MI",
      "destination": "Lansing-MI",
      "path": ["Flint-MI", "Lansing-MI"],
      "demand_gbps": 5.0,
      "hop_count": 1,
      "routing_stage": "stage_a"
    }
  ]
}
```

### Example Results

From a typical run:
- **Total services**: 100
- **Stage A services**: 24 (one per edge in minimum edge cover)
- **Stage B services**: 76 (randomized Dijkstra paths)
- **Average hops**: 3-4 hops per service
- **Hop range**: 1 to 12 hops
- **Capacity utilization**: 10-15% of total network capacity

### Algorithm Properties

**Correctness Guarantees:**
1. **Capacity safety**: No edge capacity is ever exceeded
2. **Endpoint coverage**: Every node is source/destination of ≥1 service
3. **Path validity**: All paths are simple (no repeated nodes)
4. **Reproducibility**: Fixed random seed produces identical results

**Performance Characteristics:**
- Stage A time: O(n³) for maximum matching
- Stage B time: O(k · m log n) for k services, m edges, n nodes
- Memory: O(n + m) for graph storage

## REST API

The network simulator includes a comprehensive **FastAPI REST API** that exposes all network data via HTTP endpoints with interactive Swagger documentation.

### API Features

- **OpenAPI 3.0 Specification** with full Swagger UI
- **CRUD Operations** for nodes and edges
- **Analytics Endpoints** for capacity utilization and statistics
- **UUID-based identifiers** for all entities
- **Request validation** with Pydantic models
- **Comprehensive error handling** (404, 400, 409 status codes)
- **CORS enabled** for cross-origin requests

### Starting the API

**With Docker Compose (Recommended):**
```bash
docker compose up --build
# API available at http://localhost:8003
```

**Locally:**
```bash
cd network_simulator
uv run python run_api.py
# or: python -m uvicorn src.api:app --host 0.0.0.0 --port 8003
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8003/docs (interactive API testing)
- **ReDoc**: http://localhost:8003/redoc (clean API documentation)

### Available Endpoints

#### Health
- `GET /health` - API health check and database status

#### Nodes (Network Elements)
- `GET /nodes` - List all nodes (optional filters: vendor, min_capacity)
- `GET /nodes/{uuid}` - Get node by UUID
- `GET /nodes/by-name/{name}` - Get node by name
- `POST /nodes` - Create a new node
- `PUT /nodes/{uuid}` - Update node attributes
- `DELETE /nodes/{uuid}` - Delete node (if not referenced)

#### Edges (Connections)
- `GET /edges` - List all edges
- `GET /edges/{uuid}` - Get edge by UUID
- `GET /edges/by-endpoints/` - Get edge by node pair (query params)
- `POST /edges` - Create a new edge
- `DELETE /edges/{uuid}` - Delete edge (if not referenced)

#### Analytics
- `GET /analytics/stats` - Database statistics (node/edge/service counts)
- `GET /capacity/summary` - Capacity utilization for all edges
- `GET /capacity/edge/{uuid}` - Capacity utilization for specific edge
- `GET /capacity/violations` - Edges exceeding capacity

### Example API Usage

**Get all nodes:**
```bash
curl http://localhost:8003/nodes
```

**Create a new node:**
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

**Get capacity utilization:**
```bash
curl http://localhost:8003/capacity/summary
```

**Filter nodes by vendor:**
```bash
curl "http://localhost:8003/nodes?vendor=TeleConnect"
```

### API Testing

A comprehensive test suite validates all endpoints:

```bash
# Run all API tests
docker compose run --rm network-simulator pytest tests/test_api.py -v

# 41 tests covering:
# - Health endpoint
# - Node CRUD operations
# - Edge CRUD operations
# - Service CRUD operations
# - Analytics queries
# - Error handling
```

### Complete API Usage Guide

For detailed API documentation, examples, and best practices, see **[API_GUIDE.md](API_GUIDE.md)**.

The guide includes:
- Quick start tutorials
- Complete endpoint reference
- Common workflows and examples
- Error handling patterns
- Python code examples
- Advanced usage patterns
- Monitoring scripts

## Future Enhancements

Future phases could add:

- **Service Visualization**: Overlay service paths on network map
- **Network Failure Scenarios**: Simulate node/link failures and rerouting
- **Dynamic Traffic**: Time-varying traffic patterns and congestion modeling
- **Quality of Service (QoS)**: Prioritization and bandwidth management
- **Path Optimization**: Multi-objective routing (latency, cost, reliability)

## License

For educational/demonstration purposes only.
