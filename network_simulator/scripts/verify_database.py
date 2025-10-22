"""
Database verification script.
Validates all constraints on services, nodes, and edges using SQL queries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.database_manager import NetworkDatabase


def verify_database(db: NetworkDatabase) -> bool:
    """
    Run comprehensive verification checks on database.

    Returns:
        True if all checks pass, False otherwise
    """
    print("=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    errors = []
    warnings = []

    # Check 1: Referential Integrity
    print("\n[CHECK 1/7] Referential Integrity")
    print("-" * 70)
    cursor = db.conn.cursor()

    # Check for orphaned services (invalid source/dest)
    cursor.execute("""
        SELECT COUNT(*) FROM services s
        WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = s.source_node_uuid)
           OR NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = s.destination_node_uuid)
    """)
    orphaned_services = cursor.fetchone()[0]

    # Check for orphaned edges (invalid endpoints)
    cursor.execute("""
        SELECT COUNT(*) FROM edges e
        WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = e.node1_uuid)
           OR NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = e.node2_uuid)
    """)
    orphaned_edges = cursor.fetchone()[0]

    # Check for orphaned path nodes
    cursor.execute("""
        SELECT COUNT(*) FROM service_path_nodes spn
        WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE uuid = spn.node_uuid)
           OR NOT EXISTS (SELECT 1 FROM services WHERE uuid = spn.service_uuid)
    """)
    orphaned_path_nodes = cursor.fetchone()[0]

    if orphaned_services == 0 and orphaned_edges == 0 and orphaned_path_nodes == 0:
        print("All references are valid")
    else:
        print(f"Found referential integrity issues:")
        if orphaned_services > 0:
            errors.append(f"{orphaned_services} services have invalid node references")
        if orphaned_edges > 0:
            errors.append(f"{orphaned_edges} edges have invalid node references")
        if orphaned_path_nodes > 0:
            errors.append(f"{orphaned_path_nodes} path nodes have invalid references")

    # Check 2: Capacity Constraints
    print("\n[CHECK 2/7] Capacity Constraints")
    print("-" * 70)
    violations = db.verify_capacity_constraints()
    if len(violations) == 0:
        print("All capacity constraints satisfied")

        # Show utilization stats
        utils = db.get_all_edge_utilizations()
        utilized = [u for u in utils if u['service_count'] > 0]
        if utilized:
            avg_util = sum(u['utilization_pct'] for u in utilized) / len(utilized)
            max_util = max(u['utilization_pct'] for u in utilized)
            print(f"  Average utilization: {avg_util:.1f}%")
            print(f"  Maximum utilization: {max_util:.1f}%")
    else:
        print(f"{len(violations)} capacity violations found")
        for v in violations[:3]:
            errors.append(f"Edge {v['edge_uuid']}: overage {v['overage']:.2f} Gbps")

    # Check 3: Endpoint Coverage
    print("\n[CHECK 3/7] Endpoint Coverage")
    print("-" * 70)
    cursor.execute("""
        SELECT COUNT(*) FROM nodes n
        WHERE NOT EXISTS (
            SELECT 1 FROM services
            WHERE source_node_uuid = n.uuid OR destination_node_uuid = n.uuid
        )
    """)
    uncovered_nodes = cursor.fetchone()[0]

    if uncovered_nodes == 0:
        print("All 48 nodes covered as endpoints")
    else:
        print(f"{uncovered_nodes} nodes not covered as endpoints")
        errors.append(f"{uncovered_nodes} nodes are not service endpoints")

    # Check 4: Path Validity
    print("\n[CHECK 4/7] Path Validity")
    print("-" * 70)

    # Check paths start at source
    cursor.execute("""
        SELECT COUNT(*) FROM services s
        JOIN service_path_nodes spn ON s.uuid = spn.service_uuid
        WHERE spn.sequence_order = 0 AND spn.node_uuid != s.source_node_uuid
    """)
    invalid_starts = cursor.fetchone()[0]

    # Check paths end at destination
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

    # Check for path cycles (repeated nodes)
    cursor.execute("""
        SELECT service_uuid, COUNT(DISTINCT node_uuid) as unique_nodes, COUNT(*) as total_nodes
        FROM service_path_nodes
        GROUP BY service_uuid
        HAVING unique_nodes != total_nodes
    """)
    cyclic_paths = cursor.fetchall()

    if invalid_starts == 0 and invalid_ends == 0 and len(cyclic_paths) == 0:
        print("All paths are valid (simple, correct endpoints)")
    else:
        if invalid_starts > 0:
            errors.append(f"{invalid_starts} paths don't start at source")
        if invalid_ends > 0:
            errors.append(f"{invalid_ends} paths don't end at destination")
        if len(cyclic_paths) > 0:
            errors.append(f"{len(cyclic_paths)} paths have cycles")

    # Check 5: Edge Connectivity
    print("\n[CHECK 5/7] Edge Connectivity")
    print("-" * 70)

    # Check that consecutive path nodes have edges
    cursor.execute("""
        SELECT s.uuid, s.name
        FROM services s
        JOIN service_path_nodes spn1 ON s.uuid = spn1.service_uuid
        JOIN service_path_nodes spn2 ON s.uuid = spn2.service_uuid
        WHERE spn2.sequence_order = spn1.sequence_order + 1
          AND NOT EXISTS (
              SELECT 1 FROM edges e
              WHERE (e.node1_uuid = spn1.node_uuid AND e.node2_uuid = spn2.node_uuid)
                 OR (e.node1_uuid = spn2.node_uuid AND e.node2_uuid = spn1.node_uuid)
          )
        LIMIT 5
    """)
    disconnected_paths = cursor.fetchall()

    if len(disconnected_paths) == 0:
        print("All path segments use valid edges")
    else:
        print(f"Found {len(disconnected_paths)} services with disconnected paths")
        for svc in disconnected_paths:
            errors.append(f"Service {svc[1]} has disconnected path")

    # Check 6: UUID Uniqueness
    print("\n[CHECK 6/7] UUID Uniqueness")
    print("-" * 70)

    # Check node UUIDs are unique
    cursor.execute("SELECT COUNT(DISTINCT uuid) FROM nodes")
    unique_node_uuids = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM nodes")
    total_nodes = cursor.fetchone()[0]

    # Check edge UUIDs are unique
    cursor.execute("SELECT COUNT(DISTINCT uuid) FROM edges")
    unique_edge_uuids = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM edges")
    total_edges = cursor.fetchone()[0]

    # Check service UUIDs are unique
    cursor.execute("SELECT COUNT(DISTINCT uuid) FROM services")
    unique_service_uuids = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM services")
    total_services = cursor.fetchone()[0]

    if (unique_node_uuids == total_nodes and
        unique_edge_uuids == total_edges and
        unique_service_uuids == total_services):
        print("All UUIDs are unique")
        print(f"  Nodes: {total_nodes} unique UUIDs")
        print(f"  Edges: {total_edges} unique UUIDs")
        print(f"  Services: {total_services} unique UUIDs")
    else:
        if unique_node_uuids != total_nodes:
            errors.append(f"Duplicate node UUIDs: {total_nodes - unique_node_uuids}")
        if unique_edge_uuids != total_edges:
            errors.append(f"Duplicate edge UUIDs: {total_edges - unique_edge_uuids}")
        if unique_service_uuids != total_services:
            errors.append(f"Duplicate service UUIDs: {total_services - unique_service_uuids}")

    # Check 7: Data Constraints
    print("\n[CHECK 7/7] Data Constraints")
    print("-" * 70)

    # Check for negative capacities
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE capacity_gbps <= 0")
    invalid_node_capacity = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM edges WHERE capacity_gbps <= 0")
    invalid_edge_capacity = cursor.fetchone()[0]

    # Check for invalid hop counts
    cursor.execute("SELECT COUNT(*) FROM services WHERE hop_count < 1")
    invalid_hop_count = cursor.fetchone()[0]

    # Check source != destination
    cursor.execute("SELECT COUNT(*) FROM services WHERE source_node_uuid = destination_node_uuid")
    same_endpoints = cursor.fetchone()[0]

    if (invalid_node_capacity == 0 and invalid_edge_capacity == 0 and
        invalid_hop_count == 0 and same_endpoints == 0):
        print("All data constraints satisfied")
    else:
        if invalid_node_capacity > 0:
            errors.append(f"{invalid_node_capacity} nodes have invalid capacity")
        if invalid_edge_capacity > 0:
            errors.append(f"{invalid_edge_capacity} edges have invalid capacity")
        if invalid_hop_count > 0:
            errors.append(f"{invalid_hop_count} services have invalid hop count")
        if same_endpoints > 0:
            errors.append(f"{same_endpoints} services have same source and destination")

    cursor.close()

    # Print results
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)

    if len(errors) == 0:
        print("ALL CHECKS PASSED")
        print("\nDatabase is VALID and satisfies all constraints:")
        print("  • All references are valid")
        print("  • No capacity violations")
        print("  • All nodes covered as endpoints")
        print("  • All paths use valid edges")
        print("  • All UUIDs are unique")
        print("  • All data constraints satisfied")
    else:
        print("VERIFICATION FAILED")
        print(f"\nFound {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    print("=" * 70)

    return len(errors) == 0


def main():
    """Main verification function."""
    db_path = Path("data/network.db")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    db = NetworkDatabase(str(db_path))

    passed = verify_database(db)

    # Additional statistics
    stats = db.get_stats()
    utils = db.get_all_edge_utilizations()

    print(f"\nDatabase Statistics:")
    print(f"  Total nodes:    {stats['nodes']}")
    print(f"  Total edges:    {stats['edges']}")
    print(f"  Total services: {stats['services']}")

    if stats['services'] > 0:
        utilized_edges = sum(1 for u in utils if u['service_count'] > 0)
        print(f"  Utilized edges: {utilized_edges}/{stats['edges']} ({utilized_edges/stats['edges']*100:.1f}%)")

        cursor = db.conn.cursor()
        cursor.execute("SELECT AVG(hop_count), MIN(hop_count), MAX(hop_count) FROM services")
        avg_hops, min_hops, max_hops = cursor.fetchone()
        cursor.close()

        print(f"  Hop statistics: avg={avg_hops:.2f}, min={min_hops}, max={max_hops}")

    db.close()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
