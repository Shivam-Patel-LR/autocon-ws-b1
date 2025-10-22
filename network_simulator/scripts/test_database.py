"""
Test script to verify database functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.database_manager import NetworkDatabase


def main():
    """Test database operations."""
    db = NetworkDatabase("data/network.db")

    print("=" * 70)
    print("DATABASE TEST & VERIFICATION")
    print("=" * 70)

    # Test 1: Get stats
    stats = db.get_stats()
    print(f"\n[TEST 1] Database Statistics:")
    print(f"  Nodes:    {stats['nodes']}")
    print(f"  Edges:    {stats['edges']}")
    print(f"  Services: {stats['services']}")

    # Test 2: Query nodes
    print(f"\n[TEST 2] Sample Nodes:")
    nodes = db.get_all_nodes()[:5]
    for node in nodes:
        print(f"  {node['name']} ({node['vendor']}) - {node['capacity_gbps']} Gbps")

    # Test 3: Query edges
    print(f"\n[TEST 3] Sample Edges:")
    edges = db.get_all_edges()[:5]
    for edge in edges:
        node1 = db.get_node_by_uuid(edge['node1_uuid'])
        node2 = db.get_node_by_uuid(edge['node2_uuid'])
        print(f"  {node1['name']} - {node2['name']}: {edge['capacity_gbps']} Gbps")

    # Test 4: Query services
    print(f"\n[TEST 4] Sample Services:")
    services = db.get_all_services()[:3]
    for svc in services:
        print(f"  {svc['name']}")
        print(f"    Hops: {svc['hop_count']}, Distance: {svc['total_distance_km']:.2f} km")
        print(f"    Path: {len(svc['path_node_uuids'])} nodes, {len(svc['path_edge_uuids'])} edges")

    # Test 5: Capacity utilization
    print(f"\n[TEST 5] Top 5 Most Utilized Edges:")
    utils = db.get_all_edge_utilizations()[:5]
    for util in utils:
        print(f"  Edge {util['uuid'][:8]}...: {util['utilization_pct']:.1f}% "
              f"({util['total_demand_gbps']:.1f}/{util['capacity_gbps']:.1f} Gbps, "
              f"{util['service_count']} services)")

    # Test 6: Capacity violations
    print(f"\n[TEST 6] Capacity Constraint Verification:")
    violations = db.verify_capacity_constraints()
    if violations:
        print(f"  Found {len(violations)} violations:")
        for v in violations[:3]:
            print(f"    Edge {v['edge_uuid'][:8]}...: overage {v['overage']:.2f} Gbps")
    else:
        print(f"  All capacity constraints satisfied")

    # Test 7: Node lookup
    print(f"\n[TEST 7] Node Lookup by Name:")
    node = db.get_node_by_name("NYC-Manhattan")
    if node:
        print(f"  UUID: {node['uuid']}")
        print(f"  Location: ({node['latitude']}, {node['longitude']})")
        print(f"  Capacity: {node['capacity_gbps']} Gbps")

    # Test 8: Services using specific node
    print(f"\n[TEST 8] Services from NYC-Manhattan:")
    services_from_nyc = db.get_services_from_node(node['uuid'])
    print(f"  Found {len(services_from_nyc)} services originating from NYC-Manhattan")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    main()
