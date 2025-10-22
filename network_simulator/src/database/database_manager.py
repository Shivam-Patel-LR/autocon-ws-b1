"""
SQLite database manager for network simulator.
Provides unified access to nodes, edges, and services with transaction support.
"""

import sqlite3
import uuid as uuid_module
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager


class NetworkDatabase:
    """
    Unified database manager for all network data operations.

    Manages nodes, edges, and services in a single SQLite database with
    referential integrity, transaction support, and optimized queries.
    """

    def __init__(self, db_path: str = "data/network.db", auto_init: bool = True):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
            auto_init: If True, create schema if database doesn't exist
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()

        if auto_init:
            self._init_schema()

    def _connect(self) -> None:
        """Initialize database connection with optimal settings."""
        # Create parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access

        # Enable foreign key constraints
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Use write-ahead logging for better concurrency
        self.conn.execute("PRAGMA journal_mode = WAL")

        # Balance between safety and performance
        self.conn.execute("PRAGMA synchronous = NORMAL")

    def _init_schema(self) -> None:
        """Create database schema if tables don't exist."""
        cursor = self.conn.cursor()

        # Create nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                uuid TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                vendor TEXT NOT NULL,
                capacity_gbps REAL NOT NULL CHECK(capacity_gbps > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_vendor ON nodes(vendor)")

        # Create edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                uuid TEXT PRIMARY KEY,
                node1_uuid TEXT NOT NULL,
                node2_uuid TEXT NOT NULL,
                capacity_gbps REAL NOT NULL CHECK(capacity_gbps > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node1_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
                FOREIGN KEY (node2_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
                CHECK(node1_uuid < node2_uuid),
                UNIQUE(node1_uuid, node2_uuid)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_node1 ON edges(node1_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_node2 ON edges(node2_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_endpoints ON edges(node1_uuid, node2_uuid)")

        # Create services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                uuid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_node_uuid TEXT NOT NULL,
                destination_node_uuid TEXT NOT NULL,
                demand_gbps REAL NOT NULL CHECK(demand_gbps > 0),
                hop_count INTEGER NOT NULL CHECK(hop_count >= 1),
                total_distance_km REAL NOT NULL CHECK(total_distance_km >= 0),
                service_timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
                FOREIGN KEY (destination_node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT,
                CHECK(source_node_uuid != destination_node_uuid)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_source ON services(source_node_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_destination ON services(destination_node_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_timestamp ON services(service_timestamp)")

        # Create service_path_nodes junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_path_nodes (
                service_uuid TEXT NOT NULL,
                sequence_order INTEGER NOT NULL CHECK(sequence_order >= 0),
                node_uuid TEXT NOT NULL,
                PRIMARY KEY (service_uuid, sequence_order),
                FOREIGN KEY (service_uuid) REFERENCES services(uuid) ON DELETE CASCADE,
                FOREIGN KEY (node_uuid) REFERENCES nodes(uuid) ON DELETE RESTRICT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_paths_service ON service_path_nodes(service_uuid)")

        # Create service_path_edges junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_path_edges (
                service_uuid TEXT NOT NULL,
                sequence_order INTEGER NOT NULL CHECK(sequence_order >= 0),
                edge_uuid TEXT NOT NULL,
                PRIMARY KEY (service_uuid, sequence_order),
                FOREIGN KEY (service_uuid) REFERENCES services(uuid) ON DELETE CASCADE,
                FOREIGN KEY (edge_uuid) REFERENCES edges(uuid) ON DELETE RESTRICT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_edges_service ON service_path_edges(service_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_edges_edge ON service_path_edges(edge_uuid)")

        # Create capacity_utilization table for pre-computed metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capacity_utilization (
                edge_uuid TEXT PRIMARY KEY,
                total_demand_gbps REAL DEFAULT 0,
                service_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (edge_uuid) REFERENCES edges(uuid) ON DELETE CASCADE
            )
        """)

        # Create views for convenient queries
        cursor.execute("DROP VIEW IF EXISTS edge_details")
        cursor.execute("""
            CREATE VIEW edge_details AS
            SELECT
                e.uuid AS edge_uuid,
                n1.name AS node1_name,
                n2.name AS node2_name,
                e.capacity_gbps,
                e.created_at
            FROM edges e
            JOIN nodes n1 ON e.node1_uuid = n1.uuid
            JOIN nodes n2 ON e.node2_uuid = n2.uuid
        """)

        cursor.execute("DROP VIEW IF EXISTS service_details")
        cursor.execute("""
            CREATE VIEW service_details AS
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
            JOIN nodes n2 ON s.destination_node_uuid = n2.uuid
        """)

        cursor.execute("DROP VIEW IF EXISTS capacity_summary")
        cursor.execute("""
            CREATE VIEW capacity_summary AS
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
        """)

        self.conn.commit()
        cursor.close()

    # ==================== NODE OPERATIONS ====================

    def insert_node(
        self,
        node_uuid: str,
        name: str,
        latitude: float,
        longitude: float,
        vendor: str,
        capacity_gbps: float
    ) -> None:
        """Insert a new node into the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO nodes (uuid, name, latitude, longitude, vendor, capacity_gbps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (node_uuid, name, latitude, longitude, vendor, capacity_gbps))
        self.conn.commit()
        cursor.close()

    def get_node_by_uuid(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        """Get node by UUID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE uuid = ?", (node_uuid,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_node_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get node by name (exact match)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE name = ?", (name,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def search_nodes_by_name(self, name_substring: str) -> List[Dict[str, Any]]:
        """
        Search for nodes by name substring (case-insensitive).

        Args:
            name_substring: Substring to search for in node names

        Returns:
            List of nodes where name contains the substring (case-insensitive)
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM nodes WHERE name LIKE ? COLLATE NOCASE ORDER BY name",
            (f"%{name_substring}%",)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes ORDER BY name")
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    def node_uuid_from_name(self, name: str) -> Optional[str]:
        """Get node UUID from name (convenience method)."""
        node = self.get_node_by_name(name)
        return node['uuid'] if node else None

    #==================== EDGE OPERATIONS ====================

    def insert_edge(
        self,
        edge_uuid: str,
        node1_uuid: str,
        node2_uuid: str,
        capacity_gbps: float
    ) -> None:
        """Insert a new edge into the database."""
        # Ensure canonical ordering
        if node1_uuid > node2_uuid:
            node1_uuid, node2_uuid = node2_uuid, node1_uuid

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO edges (uuid, node1_uuid, node2_uuid, capacity_gbps)
            VALUES (?, ?, ?, ?)
        """, (edge_uuid, node1_uuid, node2_uuid, capacity_gbps))

        # Initialize capacity utilization entry
        cursor.execute("""
            INSERT INTO capacity_utilization (edge_uuid, total_demand_gbps, service_count)
            VALUES (?, 0, 0)
        """, (edge_uuid,))

        self.conn.commit()
        cursor.close()

    def get_edge_by_uuid(self, edge_uuid: str) -> Optional[Dict[str, Any]]:
        """Get edge by UUID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM edges WHERE uuid = ?", (edge_uuid,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_edge_by_endpoints(
        self,
        node1_uuid: str,
        node2_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """Get edge by endpoint UUIDs."""
        # Ensure canonical ordering
        if node1_uuid > node2_uuid:
            node1_uuid, node2_uuid = node2_uuid, node1_uuid

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM edges
            WHERE node1_uuid = ? AND node2_uuid = ?
        """, (node1_uuid, node2_uuid))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_all_edges(self) -> List[Dict[str, Any]]:
        """Get all edges."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM edges ORDER BY node1_uuid, node2_uuid")
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    def get_edge_uuid(self, node1_uuid: str, node2_uuid: str) -> Optional[str]:
        """Get edge UUID from endpoints (convenience method)."""
        edge = self.get_edge_by_endpoints(node1_uuid, node2_uuid)
        return edge['uuid'] if edge else None

    # ==================== SERVICE OPERATIONS ====================

    def insert_service_with_path(
        self,
        service_uuid: str,
        name: str,
        source_node_uuid: str,
        destination_node_uuid: str,
        demand_gbps: float,
        hop_count: int,
        total_distance_km: float,
        service_timestamp: str,
        path_node_uuids: List[str],
        path_edge_uuids: List[str]
    ) -> None:
        """
        Insert service with its complete path atomically.

        Uses a transaction to ensure all-or-nothing insertion.
        """
        cursor = self.conn.cursor()

        try:
            # Insert service
            cursor.execute("""
                INSERT INTO services (
                    uuid, name, source_node_uuid, destination_node_uuid,
                    demand_gbps, hop_count, total_distance_km,
                    service_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (service_uuid, name, source_node_uuid, destination_node_uuid,
                  demand_gbps, hop_count, total_distance_km,
                  service_timestamp))

            # Insert path nodes
            for seq, node_uuid in enumerate(path_node_uuids):
                cursor.execute("""
                    INSERT INTO service_path_nodes (service_uuid, sequence_order, node_uuid)
                    VALUES (?, ?, ?)
                """, (service_uuid, seq, node_uuid))

            # Insert path edges
            for seq, edge_uuid in enumerate(path_edge_uuids):
                cursor.execute("""
                    INSERT INTO service_path_edges (service_uuid, sequence_order, edge_uuid)
                    VALUES (?, ?, ?)
                """, (service_uuid, seq, edge_uuid))

                # Update capacity utilization
                cursor.execute("""
                    UPDATE capacity_utilization
                    SET total_demand_gbps = total_demand_gbps + ?,
                        service_count = service_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE edge_uuid = ?
                """, (demand_gbps, edge_uuid))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def get_service_by_uuid(self, service_uuid: str) -> Optional[Dict[str, Any]]:
        """Get service with its complete path."""
        cursor = self.conn.cursor()

        # Get service info
        cursor.execute("SELECT * FROM services WHERE uuid = ?", (service_uuid,))
        service_row = cursor.fetchone()
        if not service_row:
            cursor.close()
            return None

        service = dict(service_row)

        # Get path nodes
        cursor.execute("""
            SELECT node_uuid FROM service_path_nodes
            WHERE service_uuid = ?
            ORDER BY sequence_order
        """, (service_uuid,))
        service['path_node_uuids'] = [row['node_uuid'] for row in cursor.fetchall()]

        # Get path edges
        cursor.execute("""
            SELECT edge_uuid FROM service_path_edges
            WHERE service_uuid = ?
            ORDER BY sequence_order
        """, (service_uuid,))
        service['path_edge_uuids'] = [row['edge_uuid'] for row in cursor.fetchall()]

        cursor.close()
        return service

    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all services with their paths."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT uuid FROM services ORDER BY service_timestamp")
        service_uuids = [row['uuid'] for row in cursor.fetchall()]
        cursor.close()

        return [self.get_service_by_uuid(uuid) for uuid in service_uuids]

    def get_services_using_edge(self, edge_uuid: str) -> List[Dict[str, Any]]:
        """Get all services that use a specific edge."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT s.*
            FROM services s
            JOIN service_path_edges spe ON s.uuid = spe.service_uuid
            WHERE spe.edge_uuid = ?
            ORDER BY s.service_timestamp
        """, (edge_uuid,))
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    def get_services_from_node(self, node_uuid: str) -> List[Dict[str, Any]]:
        """Get all services originating from a specific node."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM services
            WHERE source_node_uuid = ?
            ORDER BY service_timestamp
        """, (node_uuid,))
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    # ==================== CAPACITY QUERIES ====================

    def get_node_utilizations(self) -> Dict[str, float]:
        """
        Calculate capacity utilization for all nodes.

        Node capacity represents the outbound capacity for services originating from that node.
        This sums the demand_gbps for all services where the node is the source.

        Returns:
            Dictionary mapping node UUID to total demand in Gbps
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                source_node_uuid,
                SUM(demand_gbps) AS total_demand_gbps
            FROM services
            GROUP BY source_node_uuid
        """)
        rows = cursor.fetchall()
        cursor.close()

        utilizations = {}
        for row in rows:
            utilizations[row['source_node_uuid']] = row['total_demand_gbps']

        return utilizations

    def get_all_nodes_with_utilization(self) -> List[Dict[str, Any]]:
        """
        Get all nodes with free capacity calculated.

        Returns:
            List of node dictionaries with additional 'free_capacity_gbps' field
        """
        nodes = self.get_all_nodes()
        utilizations = self.get_node_utilizations()

        # Enrich nodes with free capacity
        for node in nodes:
            node_uuid = node['uuid']
            used_capacity = utilizations.get(node_uuid, 0.0)
            node['free_capacity_gbps'] = max(0.0, node['capacity_gbps'] - used_capacity)

        return nodes

    def get_edge_utilization(self, edge_uuid: str) -> Optional[Dict[str, Any]]:
        """Get capacity utilization for a specific edge."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                e.uuid,
                e.capacity_gbps,
                cu.total_demand_gbps,
                cu.service_count,
                (cu.total_demand_gbps / e.capacity_gbps * 100) AS utilization_pct
            FROM edges e
            LEFT JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
            WHERE e.uuid = ?
        """, (edge_uuid,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_all_edge_utilizations(self) -> List[Dict[str, Any]]:
        """Get capacity utilization for all edges."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                e.uuid,
                e.capacity_gbps,
                COALESCE(cu.total_demand_gbps, 0) AS total_demand_gbps,
                COALESCE(cu.service_count, 0) AS service_count,
                COALESCE((cu.total_demand_gbps / e.capacity_gbps * 100), 0) AS utilization_pct
            FROM edges e
            LEFT JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
            ORDER BY utilization_pct DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    def verify_capacity_constraints(self) -> List[Dict[str, Any]]:
        """
        Find all capacity violations.

        Returns list of edges where total demand exceeds capacity.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                e.uuid AS edge_uuid,
                e.capacity_gbps,
                cu.total_demand_gbps,
                (cu.total_demand_gbps - e.capacity_gbps) AS overage
            FROM edges e
            JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
            WHERE cu.total_demand_gbps > e.capacity_gbps
            ORDER BY overage DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]

    # ==================== TRANSACTION MANAGEMENT ====================

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self.conn.execute("BEGIN TRANSACTION")

    def commit(self) -> None:
        """Commit current transaction."""
        self.conn.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.conn.rollback()

    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.

        Usage:
            with db.transaction():
                db.insert_node(...)
                db.insert_edge(...)
        """
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    # ==================== ROUTING HELPER METHODS ====================

    def build_network_graph(self):
        """
        Build a NetworkX graph representation of the network.

        Returns:
            NetworkX Graph with:
                - Nodes as UUIDs
                - Edges with 'uuid' attribute
                - Node attributes: latitude, longitude, name
        """
        import networkx as nx

        G = nx.Graph()

        # Add all nodes with their attributes
        nodes = self.get_all_nodes()
        for node in nodes:
            G.add_node(
                node['uuid'],
                latitude=node['latitude'],
                longitude=node['longitude'],
                name=node['name'],
                vendor=node['vendor'],
                capacity_gbps=node['capacity_gbps']
            )

        # Add all edges with their attributes
        edges = self.get_all_edges()
        for edge in edges:
            G.add_edge(
                edge['node1_uuid'],
                edge['node2_uuid'],
                uuid=edge['uuid'],
                capacity_gbps=edge['capacity_gbps']
            )

        return G

    def get_residual_capacities(self) -> Dict[str, float]:
        """
        Get residual (available) capacity for all edges.

        Returns:
            Dictionary mapping edge UUID to residual capacity in Gbps
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                e.uuid,
                e.capacity_gbps,
                COALESCE(cu.total_demand_gbps, 0) AS total_demand_gbps
            FROM edges e
            LEFT JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
        """)
        rows = cursor.fetchall()
        cursor.close()

        residual_capacities = {}
        for row in rows:
            edge_uuid = row['uuid']
            capacity = row['capacity_gbps']
            demand = row['total_demand_gbps']
            residual = capacity - demand
            residual_capacities[edge_uuid] = max(0.0, residual)

        return residual_capacities

    def get_node_coordinates_dict(self) -> Dict[str, Tuple[float, float]]:
        """
        Get node coordinates as a dictionary.

        Returns:
            Dictionary mapping node UUID to (latitude, longitude) tuple
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT uuid, latitude, longitude FROM nodes")
        rows = cursor.fetchall()
        cursor.close()

        return {row['uuid']: (row['latitude'], row['longitude']) for row in rows}

    # ==================== UTILITY METHODS ====================

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM nodes")
        node_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM services")
        service_count = cursor.fetchone()[0]

        cursor.close()

        return {
            'nodes': node_count,
            'edges': edge_count,
            'services': service_count
        }
