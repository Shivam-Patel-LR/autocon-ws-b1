# Network Simulator Database Guide

## Overview

The network simulator now uses **SQLite** as the primary data storage system with **UUID-based identifiers** for all entities (nodes, edges, services). This provides referential integrity, efficient queries, and eliminates naming conflicts.

---

## Database Architecture

### **Single Database File**: `data/network.db`

All network data is stored in a single SQLite database containing:
- **48 nodes** (network elements)
- **200 edges** (connections)
- **100+ services** (routed paths)
- **UUID registries** (bidirectional mappings)
- **Capacity utilization** (pre-computed metrics)

---

## Schema Overview

### **Tables**:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `nodes` | Network elements | uuid (PK), name (UNIQUE), lat, long, vendor, capacity_gbps |
| `edges` | Connections | uuid (PK), node1_uuid (FK), node2_uuid (FK), capacity_gbps |
| `services` | Routed services | uuid (PK), source_node_uuid (FK), destination_node_uuid (FK), demand_gbps, hop_count |
| `service_path_nodes` | Service paths | service_uuid (FK), sequence_order, node_uuid (FK) |
| `service_path_edges` | Edges used by services | service_uuid (FK), sequence_order, edge_uuid (FK) |
| `capacity_utilization` | Pre-computed metrics | edge_uuid (PK), total_demand_gbps, service_count |

### **Views**:

- `edge_details` - Edges with human-readable node names
- `service_details` - Services with node names resolved
- `capacity_summary` - Capacity utilization with percentages

---

## Quick Start

### 1. Import Existing Data (First Time Only)

```bash
# Import CSV/JSON files into database
python migrations/import_existing_data.py
```

This creates `data/network.db` and imports:
- network_elements.csv → nodes table
- adjacency_matrix.csv → edges table
- services.json → services tables (if exists)

### 2. Generate Services (Database-Driven)

```bash
# Generate 100 services directly into database
python src/generate_services_db.py
```

Services are stored with:
- Proper UUIDs for all entities
- Full path tracking (nodes and edges)
- Automatic capacity tracking

### 3. Export to JSON

```bash
# Export database to JSON with UUID registries
python migrations/export_to_json.py
```

Creates `data/services_export.json` with:
- UUID-based service references
- Complete node registry
- Complete edge registry

### 4. Verify Database Integrity

```bash
# Run comprehensive verification checks
python verify_database.py
```

Validates:
- Referential integrity
- Capacity constraints
- Endpoint coverage
- Path validity
- UUID uniqueness

---

## JSON Export Format

### Complete Structure:

```json
{
  "metadata": {
    "total_services": 100,
    "demand_per_service_gbps": 5.0,
    "stage_a_services": 24,
    "stage_b_services": 76,
    "database_export": true,
    "export_timestamp": "2025-10-14T21:25:54Z"
  },

  "registries": {
    "nodes": {
      "f9581593-4f1f-4da5-83ba-73aacd2cc101": {
        "name": "Akron-OH",
        "latitude": 41.0814,
        "longitude": -81.519,
        "vendor": "TeleConnect",
        "capacity_gbps": 520.0
      }
    },

    "edges": {
      "0c929850-79fc-4acd-a69d-163dc318353a": {
        "node_1_uuid": "0a6628a0-cfd3-4050-8a68-672c4679e952",
        "node_2_uuid": "15aa9c14-414d-4771-beb8-15c2b3c57753",
        "capacity_gbps": 43.55
      }
    }
  },

  "services": [
    {
      "service_uuid": "4b20d4ae-8932-4f05-b093-cc2202dd3e1e",
      "name": "Service Buffalo-Downtown to Toledo-Downtown",
      "source_node_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
      "destination_node_uuid": "da3f413a-7b53-43b8-ab49-793a6cdddadb",
      "path_node_uuids": [
        "7e518bf4-bf70-4e95-a164-0697b07795b1",
        "a05da56a-becd-43b8-8d0a-172da8342f59",
        "ba1221ba-ae4c-4a5e-adbb-6ad86ae52775",
        "b04f0c10-7922-4275-8fdf-53997e6c32a2",
        "da3f413a-7b53-43b8-ab49-793a6cdddadb"
      ],
      "path_edge_uuids": [
        "12de945f-5a3a-4818-939c-5a2977c653e7",
        "73d4b638-f882-4201-91e3-07ec165cda87",
        "b9781101-7b10-47f1-a232-ef5ac27dbc6c",
        "9aabf558-f541-4b63-96f9-028aaed368d1"
      ],
      "demand_gbps": 5.0,
      "hop_count": 4,
      "total_distance_km": 897.19,
      "timestamp": "2023-06-15T14:32:18Z"
    }
  ]
}
```

---

## Useful SQL Queries

### Query Services Using a Specific Edge

```sql
SELECT s.name, s.demand_gbps, s.hop_count
FROM services s
JOIN service_path_edges spe ON s.uuid = spe.service_uuid
WHERE spe.edge_uuid = '<edge-uuid>'
ORDER BY s.service_timestamp;
```

### Find Capacity Violations

```sql
SELECT * FROM capacity_summary
WHERE utilization_pct > 100
ORDER BY utilization_pct DESC;
```

### Get Top 10 Most Utilized Edges

```sql
SELECT edge_name, capacity_gbps, total_demand_gbps, utilization_pct, service_count
FROM capacity_summary
ORDER BY utilization_pct DESC
LIMIT 10;
```

### Find Nodes Not Covered as Endpoints

```sql
SELECT n.name, n.capacity_gbps
FROM nodes n
WHERE NOT EXISTS (
    SELECT 1 FROM services
    WHERE source_node_uuid = n.uuid OR destination_node_uuid = n.uuid
);
```

### Get All Services from NYC-Manhattan

```sql
SELECT s.name, s.hop_count, s.total_distance_km
FROM service_details s
WHERE s.source_name = 'NYC-Manhattan'
ORDER BY s.hop_count DESC;
```

### Calculate Average Path Length by Routing Stage

```sql
SELECT routing_stage,
       COUNT(*) as count,
       AVG(hop_count) as avg_hops,
       AVG(total_distance_km) as avg_distance_km
FROM services
GROUP BY routing_stage;
```

---

## Benefits of Database Approach

### Referential Integrity
- Foreign key constraints prevent orphaned records
- Can't delete a node if services reference it
- Cascade deletes maintain consistency

### Efficient Queries
- "Which services use edge X?" - instant lookup via index
- Aggregation queries (capacity utilization) in milliseconds
- Complex joins without loading entire dataset

### Transaction Support
- Services inserted atomically with all path data
- Rollback on errors prevents partial writes
- ACID guarantees

### No Naming Conflicts
- UUIDs are globally unique
- Safe to merge datasets from different sources
- Names can change without breaking references

### Scalability
- Handles 10,000+ services efficiently
- Indexed lookups are O(log n)
- Can migrate to PostgreSQL if needed

### Single Source of Truth
- One file to backup: `network.db`
- No CSV/JSON sync issues
- Consistent data across all queries

---

## Python API Examples

### Basic Database Operations:

```python
from database.database_manager import NetworkDatabase

# Open database
db = NetworkDatabase("data/network.db")

# Get all nodes
nodes = db.get_all_nodes()
for node in nodes[:5]:
    print(f"{node['name']}: {node['capacity_gbps']} Gbps")

# Get node by name
nyc = db.get_node_by_name("NYC-Manhattan")
print(f"NYC UUID: {nyc['uuid']}")

# Get services from a node
services = db.get_services_from_node(nyc['uuid'])
print(f"Services from NYC: {len(services)}")

# Check capacity utilization
utils = db.get_all_edge_utilizations()
top_edge = utils[0]
print(f"Most utilized: {top_edge['utilization_pct']:.1f}%")

# Close connection
db.close()
```

### Using Transactions:

```python
with db.transaction():
    db.insert_node(uuid, name, lat, lon, vendor, capacity)
    db.insert_edge(edge_uuid, node1_uuid, node2_uuid, capacity)
    # Both committed together or rolled back on error
```

---

## File Structure

```
network_simulator/
├── data/
│   ├── network.db              # SQLite database (PRIMARY STORAGE)
│   ├── network_elements.csv    # Source data (import only)
│   ├── adjacency_matrix.csv    # Source data (import only)
│   └── services_export.json    # Generated exports
├── src/
│   ├── database_manager.py     # Database interface
│   ├── generate_services_db.py # Database-driven service generator
│   └── ...
├── migrations/
│   ├── 001_initial_schema.sql  # Schema definition
│   ├── import_existing_data.py # CSV → Database
│   └── export_to_json.py       # Database → JSON
├── test_database.py            # Database functionality tests
├── verify_database.py          # Constraint verification
└── clear_services.py           # Utility to reset services
```

---

## Workflow

### Complete Workflow from Scratch:

```bash
# 1. Import data into database
python migrations/import_existing_data.py

# 2. Verify import
python test_database.py

# 3. Generate services (stores in database)
python src/generate_services_db.py

# 4. Verify all constraints
python verify_database.py

# 5. Export to JSON (with UUID registries)
python migrations/export_to_json.py
```

### Regenerate Services:

```bash
# Clear existing services
python clear_services.py

# Generate new services
python src/generate_services_db.py

# Verify and export
python verify_database.py
python migrations/export_to_json.py
```

---

## Verification Checks

The database verifier (`verify_database.py`) performs 7 comprehensive checks:

1. **Referential Integrity** - All foreign keys valid
2. **Capacity Constraints** - No edge exceeds capacity
3. **Endpoint Coverage** - All nodes are service endpoints
4. **Path Validity** - Paths start/end correctly, no cycles
5. **Edge Connectivity** - All path segments use valid edges
6. **UUID Uniqueness** - All UUIDs are unique
7. **Data Constraints** - All CHECK constraints satisfied

---

## Performance

### Current Capacity:
- **Nodes**: 48
- **Edges**: 200
- **Services**: 100
- **Database Size**: ~150 KB

### Query Performance (tested):
- Node lookup by UUID: < 1ms
- Edge lookup by endpoints: < 1ms
- Services using edge X: < 5ms
- Capacity utilization for all edges: < 10ms
- Full database verification: < 100ms

### Scalability:
- Can handle **10,000+ services** efficiently
- Proper indexes ensure O(log n) lookups
- Transaction overhead is minimal
- WAL mode enables concurrent readers

---

## Advantages Over File-Based Storage

| Feature | File-Based | Database |
|---------|------------|----------|
| Referential integrity |  Manual | Enforced |
| Atomicity |  Partial writes | Transactions |
| Query speed |  O(n) linear scan | O(log n) indexed |
| Capacity checks |  Manual aggregation | Pre-computed |
| Concurrency |  File locks | WAL mode |
| Data consistency |  Manual sync | Single source |
| Backup |  Multiple files | One file |
| Schema validation |  Runtime errors | Database constraints |

---

## Migration from Old System

If you have existing CSV/JSON files:

1. Run import: `python migrations/import_existing_data.py`
2. Verify: `python verify_database.py`
3. Export if needed: `python migrations/export_to_json.py`

The database becomes the primary storage, CSV/JSON are for interchange.

---

## Future Enhancements

The database foundation enables:

- REST API: Flask/FastAPI service for querying
- Real-time monitoring: Track capacity utilization
- Historical tracking: Store service modifications
- Graph algorithms: Complex network analysis queries
- Multi-user support: Concurrent service generation
- PostgreSQL migration: If dataset grows beyond SQLite

---

## Troubleshooting

### Database locked errors:
```bash
# Database might be locked by another process
# Check for running processes
ps aux | grep python
```

### Reset database:
```bash
# Delete and reimport
rm data/network.db
python migrations/import_existing_data.py
```

### View database schema:
```python
import sqlite3
conn = sqlite3.connect("data/network.db")
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(row[0])
```

---

## Maintenance

### Backup Database:
```bash
# Simple file copy
cp data/network.db data/network_backup_$(date +%Y%m%d).db
```

### Optimize Database:
```python
db = NetworkDatabase("data/network.db")
db.conn.execute("VACUUM")  # Reclaim space
db.conn.execute("ANALYZE")  # Update query planner statistics
```

### Export for Version Control:
```bash
# Export to JSON for git tracking
python migrations/export_to_json.py
git add data/services_export.json
```

---

## Summary

The database migration provides:
- UUID-based identifiers for all entities
- Referential integrity via foreign keys
- Transaction support for atomic operations
- Efficient queries with proper indexing
- Single source of truth in network.db
- Full verification via SQL constraints
- JSON export for compatibility

The system successfully generated 100 services with:
- All capacity constraints satisfied
- All 48 nodes covered as endpoints
- All UUIDs unique and properly referenced
- Full path tracking with node and edge UUIDs
