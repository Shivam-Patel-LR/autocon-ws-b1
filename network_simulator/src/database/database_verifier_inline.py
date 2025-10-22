"""
Inline database verifier for container initialization.
Runs all 7 verification checks without requiring standalone script.
"""

from database.database_manager import NetworkDatabase
from typing import List, Dict


class DatabaseVerifier:
    """
    Inline database verification for container initialization.

    Runs comprehensive checks on database integrity and constraint satisfaction.
    """

    def __init__(self, db: NetworkDatabase, verbose: bool = True):
        """
        Initialize verifier.

        Args:
            db: NetworkDatabase instance
            verbose: If True, print detailed progress
        """
        self.db = db
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def verify_all(self) -> bool:
        """
        Run all 7 verification checks.

        Returns:
            True if all checks pass, False otherwise
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("DATABASE VERIFICATION")
            print("=" * 70)

        self.errors = []
        self.warnings = []

        # Run all checks
        self._check_referential_integrity()
        self._check_capacity_constraints()
        self._check_endpoint_coverage()
        self._check_path_validity()
        self._check_edge_connectivity()
        self._check_uuid_uniqueness()
        self._check_data_constraints()

        # Print results
        if self.verbose:
            self._print_results()

        return len(self.errors) == 0

    def _check_referential_integrity(self) -> None:
        """Check 1: Referential Integrity."""
        if self.verbose:
            print("\n[CHECK 1/7] Referential Integrity")
            print("-" * 70)

        cursor = self.db.conn.cursor()

        # Orphaned services
        cursor.execute("""
            SELECT COUNT(*) FROM services s
            WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = s.source_node_uuid)
               OR NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = s.destination_node_uuid)
        """)
        orphaned_services = cursor.fetchone()[0]

        # Orphaned edges
        cursor.execute("""
            SELECT COUNT(*) FROM edges e
            WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = e.node1_uuid)
               OR NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = e.node2_uuid)
        """)
        orphaned_edges = cursor.fetchone()[0]

        if orphaned_services == 0 and orphaned_edges == 0:
            if self.verbose:
                print("All references are valid")
        else:
            if orphaned_services > 0:
                self.errors.append(f"{orphaned_services} services have invalid node references")
            if orphaned_edges > 0:
                self.errors.append(f"{orphaned_edges} edges have invalid node references")

        cursor.close()

    def _check_capacity_constraints(self) -> None:
        """Check 2: Capacity Constraints."""
        if self.verbose:
            print("\n[CHECK 2/7] Capacity Constraints")
            print("-" * 70)

        violations = self.db.verify_capacity_constraints()

        if len(violations) == 0:
            if self.verbose:
                print("All capacity constraints satisfied")
                utils = self.db.get_all_edge_utilizations()
                utilized = [u for u in utils if u['service_count'] > 0]
                if utilized:
                    avg_util = sum(u['utilization_pct'] for u in utilized) / len(utilized)
                    max_util = max(u['utilization_pct'] for u in utilized)
                    print(f"  Average utilization: {avg_util:.1f}%")
                    print(f"  Maximum utilization: {max_util:.1f}%")
        else:
            for v in violations[:5]:
                self.errors.append(f"Edge {v['edge_uuid'][:8]}...: overage {v['overage']:.2f} Gbps")
            if len(violations) > 5:
                self.errors.append(f"... and {len(violations) - 5} more violations")

    def _check_endpoint_coverage(self) -> None:
        """Check 3: Endpoint Coverage."""
        if self.verbose:
            print("\n[CHECK 3/7] Endpoint Coverage")
            print("-" * 70)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM nodes n
            WHERE NOT EXISTS (
                SELECT 1 FROM services
                WHERE source_node_uuid = n.uuid OR destination_node_uuid = n.uuid
            )
        """)
        uncovered_nodes = cursor.fetchone()[0]
        cursor.close()

        stats = self.db.get_stats()
        total_nodes = stats['nodes']

        if uncovered_nodes == 0:
            if self.verbose:
                print(f"All {total_nodes} nodes covered as endpoints")
        else:
            self.errors.append(f"{uncovered_nodes} nodes not covered as endpoints")

    def _check_path_validity(self) -> None:
        """Check 4: Path Validity."""
        if self.verbose:
            print("\n[CHECK 4/7] Path Validity")
            print("-" * 70)

        cursor = self.db.conn.cursor()

        # Paths start at source
        cursor.execute("""
            SELECT COUNT(*) FROM services s
            JOIN service_path_nodes spn ON s.uuid = spn.service_uuid
            WHERE spn.sequence_order = 0 AND spn.node_uuid != s.source_node_uuid
        """)
        invalid_starts = cursor.fetchone()[0]

        # Paths end at destination
        cursor.execute("""
            SELECT COUNT(*) FROM services s
            WHERE NOT EXISTS (
                SELECT 1 FROM service_path_nodes spn
                WHERE spn.service_uuid = s.uuid
                  AND spn.sequence_order = s.hop_count
                  AND spn.node_uuid = s.destination_node_uuid
            )
        """)
        invalid_ends = cursor.fetchone()[0]

        # Check for cycles
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT service_uuid, COUNT(DISTINCT node_uuid) as unique_nodes, COUNT(*) as total_nodes
                FROM service_path_nodes
                GROUP BY service_uuid
                HAVING unique_nodes != total_nodes
            )
        """)
        cyclic_paths = cursor.fetchone()[0]

        cursor.close()

        if invalid_starts == 0 and invalid_ends == 0 and cyclic_paths == 0:
            if self.verbose:
                print("All paths are valid (simple, correct endpoints)")
        else:
            if invalid_starts > 0:
                self.errors.append(f"{invalid_starts} paths don't start at source")
            if invalid_ends > 0:
                self.errors.append(f"{invalid_ends} paths don't end at destination")
            if cyclic_paths > 0:
                self.errors.append(f"{cyclic_paths} paths have cycles")

    def _check_edge_connectivity(self) -> None:
        """Check 5: Edge Connectivity."""
        if self.verbose:
            print("\n[CHECK 5/7] Edge Connectivity")
            print("-" * 70)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT s.uuid
                FROM services s
                JOIN service_path_nodes spn1 ON s.uuid = spn1.service_uuid
                JOIN service_path_nodes spn2 ON s.uuid = spn2.service_uuid
                WHERE spn2.sequence_order = spn1.sequence_order + 1
                  AND NOT EXISTS (
                      SELECT 1 FROM edges e
                      WHERE (e.node1_uuid = spn1.node_uuid AND e.node2_uuid = spn2.node_uuid)
                         OR (e.node1_uuid = spn2.node_uuid AND e.node2_uuid = spn1.node_uuid)
                  )
                LIMIT 1
            )
        """)
        disconnected_count = cursor.fetchone()[0]
        cursor.close()

        if disconnected_count == 0:
            if self.verbose:
                print("All path segments use valid edges")
        else:
            self.errors.append(f"Found services with disconnected paths")

    def _check_uuid_uniqueness(self) -> None:
        """Check 6: UUID Uniqueness."""
        if self.verbose:
            print("\n[CHECK 6/7] UUID Uniqueness")
            print("-" * 70)

        cursor = self.db.conn.cursor()

        # Check each table
        cursor.execute("SELECT COUNT(DISTINCT uuid), COUNT(*) FROM nodes")
        unique_nodes, total_nodes = cursor.fetchone()

        cursor.execute("SELECT COUNT(DISTINCT uuid), COUNT(*) FROM edges")
        unique_edges, total_edges = cursor.fetchone()

        cursor.execute("SELECT COUNT(DISTINCT uuid), COUNT(*) FROM services")
        unique_services, total_services = cursor.fetchone()

        cursor.close()

        if (unique_nodes == total_nodes and
            unique_edges == total_edges and
            unique_services == total_services):
            if self.verbose:
                print("All UUIDs are unique")
                print(f"  Nodes: {total_nodes}, Edges: {total_edges}, Services: {total_services}")
        else:
            if unique_nodes != total_nodes:
                self.errors.append(f"Duplicate node UUIDs: {total_nodes - unique_nodes}")
            if unique_edges != total_edges:
                self.errors.append(f"Duplicate edge UUIDs: {total_edges - unique_edges}")
            if unique_services != total_services:
                self.errors.append(f"Duplicate service UUIDs: {total_services - unique_services}")

    def _check_data_constraints(self) -> None:
        """Check 7: Data Constraints."""
        if self.verbose:
            print("\n[CHECK 7/7] Data Constraints")
            print("-" * 70)

        cursor = self.db.conn.cursor()

        # Check constraints
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE capacity_gbps <= 0")
        invalid_node_cap = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges WHERE capacity_gbps <= 0")
        invalid_edge_cap = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM services WHERE hop_count < 1")
        invalid_hops = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM services WHERE source_node_uuid = destination_node_uuid")
        same_endpoints = cursor.fetchone()[0]

        cursor.close()

        if (invalid_node_cap == 0 and invalid_edge_cap == 0 and
            invalid_hops == 0 and same_endpoints == 0):
            if self.verbose:
                print("All data constraints satisfied")
        else:
            if invalid_node_cap > 0:
                self.errors.append(f"{invalid_node_cap} nodes have invalid capacity")
            if invalid_edge_cap > 0:
                self.errors.append(f"{invalid_edge_cap} edges have invalid capacity")
            if invalid_hops > 0:
                self.errors.append(f"{invalid_hops} services have invalid hop count")
            if same_endpoints > 0:
                self.errors.append(f"{same_endpoints} services have same source/destination")

    def _print_results(self) -> None:
        """Print verification results summary."""
        print("\n" + "=" * 70)
        print("VERIFICATION RESULTS")
        print("=" * 70)

        if len(self.errors) == 0:
            print("ALL CHECKS PASSED")
        else:
            print("VERIFICATION FAILED")
            print(f"\nFound {len(self.errors)} error(s):")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

        print("=" * 70)
