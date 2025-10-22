-- Network Simulator Database Schema
-- Version: 1.0
-- Created: 2025-10-14

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ========== NODES TABLE ==========
-- Stores network element information
CREATE TABLE IF NOT EXISTS nodes (
    uuid TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    vendor TEXT NOT NULL,
    capacity_gbps REAL NOT NULL CHECK(capacity_gbps > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_vendor ON nodes(vendor);

-- ========== EDGES TABLE ==========
-- Stores connections between nodes
CREATE TABLE IF NOT EXISTS edges (
    uuid TEXT PRIMARY KEY,
    node1_uuid TEXT NOT NULL,
    node2_uuid TEXT NOT NULL,
    capacity_gbps REAL NOT NULL CHECK(capacity_gbps > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node1_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
    FOREIGN KEY (node2_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
    CHECK(node1_uuid < node2_uuid),  -- Canonical ordering
    UNIQUE(node1_uuid, node2_uuid)   -- No parallel edges
);

CREATE INDEX IF NOT EXISTS idx_edges_node1 ON edges(node1_uuid);
CREATE INDEX IF NOT EXISTS idx_edges_node2 ON edges(node2_uuid);
CREATE INDEX IF NOT EXISTS idx_edges_endpoints ON edges(node1_uuid, node2_uuid);

-- ========== SERVICES TABLE ==========
-- Stores generated network services
CREATE TABLE IF NOT EXISTS services (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_node_uuid TEXT NOT NULL,
    destination_node_uuid TEXT NOT NULL,
    demand_gbps REAL NOT NULL CHECK(demand_gbps > 0),
    hop_count INTEGER NOT NULL CHECK(hop_count >= 1),
    total_distance_km REAL NOT NULL CHECK(total_distance_km >= 0),
    service_timestamp TEXT NOT NULL,  -- ISO 8601 format
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
    FOREIGN KEY (destination_node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
    CHECK(source_node_uuid != destination_node_uuid)
);

CREATE INDEX IF NOT EXISTS idx_services_source ON services(source_node_uuid);
CREATE INDEX IF NOT EXISTS idx_services_destination ON services(destination_node_uuid);
CREATE INDEX IF NOT EXISTS idx_services_timestamp ON services(service_timestamp);

-- ========== SERVICE PATH NODES TABLE ==========
-- Junction table: maps services to their path nodes in order
CREATE TABLE IF NOT EXISTS service_path_nodes (
    service_uuid TEXT NOT NULL,
    sequence_order INTEGER NOT NULL CHECK(sequence_order >= 0),
    node_uuid TEXT NOT NULL,
    PRIMARY KEY (service_uuid, sequence_order),
    FOREIGN KEY (service_uuid) REFERENCES services(uuid) ON DELETE CASCADE,
    FOREIGN KEY (node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_service_paths_service ON service_path_nodes(service_uuid);

-- ========== SERVICE PATH EDGES TABLE ==========
-- Junction table: maps services to edges they use
CREATE TABLE IF NOT EXISTS service_path_edges (
    service_uuid TEXT NOT NULL,
    sequence_order INTEGER NOT NULL CHECK(sequence_order >= 0),
    edge_uuid TEXT NOT NULL,
    PRIMARY KEY (service_uuid, sequence_order),
    FOREIGN KEY (service_uuid) REFERENCES services(uuid) ON DELETE CASCADE,
    FOREIGN KEY (edge_uuid) REFERENCES edges(uuid) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_service_edges_service ON service_path_edges(service_uuid);
CREATE INDEX IF NOT EXISTS idx_service_edges_edge ON service_path_edges(edge_uuid);

-- ========== CAPACITY UTILIZATION TABLE ==========
-- Pre-computed capacity metrics for performance
CREATE TABLE IF NOT EXISTS capacity_utilization (
    edge_uuid TEXT PRIMARY KEY,
    total_demand_gbps REAL DEFAULT 0,
    service_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (edge_uuid) REFERENCES edges(uuid) ON DELETE CASCADE
);

-- ========== USEFUL VIEWS ==========

-- View: Edge details with node names
CREATE VIEW IF NOT EXISTS edge_details AS
SELECT
    e.uuid AS edge_uuid,
    n1.name AS node1_name,
    n2.name AS node2_name,
    e.capacity_gbps,
    e.created_at
FROM edges e
JOIN nodes n1 ON e.node1_uuid = n1.uuid
JOIN nodes n2 ON e.node2_uuid = n2.uuid;

-- View: Service details with node names
CREATE VIEW IF NOT EXISTS service_details AS
SELECT
    s.uuid AS service_uuid,
    s.name,
    n1.name AS source_name,
    n2.name AS destination_name,
    s.demand_gbps,
    s.hop_count,
    s.total_distance_km,
    s.service_timestamp
FROM services s
JOIN nodes n1 ON s.source_node_uuid = n1.uuid
JOIN nodes n2 ON s.destination_node_uuid = n2.uuid;

-- View: Capacity utilization with percentages
CREATE VIEW IF NOT EXISTS capacity_summary AS
SELECT
    e.uuid AS edge_uuid,
    n1.name || ' - ' || n2.name AS edge_name,
    e.capacity_gbps,
    COALESCE(cu.total_demand_gbps, 0) AS total_demand_gbps,
    COALESCE(cu.service_count, 0) AS service_count,
    COALESCE((cu.total_demand_gbps / e.capacity_gbps * 100), 0) AS utilization_pct
FROM edges e
JOIN nodes n1 ON e.node1_uuid = n1.uuid
JOIN nodes n2 ON e.node2_uuid = n2.uuid
LEFT JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
ORDER BY utilization_pct DESC;
