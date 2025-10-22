#!/usr/bin/env python3
"""
Capacity monitoring examples for Network Simulator Client.

This script demonstrates analytics and capacity tracking operations.
"""
from network_simulator_client import NetworkSimulatorClient


def main():
    """Demonstrate capacity monitoring and analytics."""

    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    print("=" * 60)
    print("Network Simulator Client - Capacity Monitoring Examples")
    print("=" * 60)

    # 1. Database Statistics
    print("\n1. Database Statistics Overview")
    print("-" * 60)
    stats = client.get_database_stats()
    print(f"Network Overview:")
    print(f"  Total Nodes: {stats.nodes}")
    print(f"  Total Edges: {stats.edges}")
    print(f"  Total Services: {stats.services}")
    print(f"  Average Services per Edge: {stats.services / stats.edges if stats.edges > 0 else 0:.2f}")

    # 2. Capacity Summary
    print("\n2. Capacity Utilization Summary (Top 10)")
    print("-" * 60)
    capacity_summary = client.get_capacity_summary()
    print(f"Total edges analyzed: {len(capacity_summary)}")

    # Show top 10 most utilized edges
    for i, edge in enumerate(capacity_summary[:10], 1):
        utilization_bar = "█" * int(edge.utilization_pct / 10)
        print(f"{i:2d}. Edge {edge.uuid[:8]}... "
              f"{edge.utilization_pct:5.1f}% {utilization_bar}")
        print(f"    Capacity: {edge.capacity_gbps:.1f} Gbps, "
              f"Demand: {edge.total_demand_gbps:.1f} Gbps, "
              f"Services: {edge.service_count}")

    # 3. High Utilization Edges
    print("\n3. High Utilization Edges (≥80%)")
    print("-" * 60)
    high_util = client.get_high_utilization_edges(threshold_pct=80.0)
    print(f"Found {len(high_util)} edges with utilization ≥80%")

    for edge in high_util[:5]:
        print(f"  Edge {edge.uuid[:8]}...: {edge.utilization_pct:.1f}% "
              f"({edge.service_count} services)")

    # 4. Capacity Violations
    print("\n4. Capacity Violations (Oversubscribed Edges)")
    print("-" * 60)
    violations = client.get_capacity_violations()

    if violations:
        print(f"⚠ WARNING: {len(violations)} edges are oversubscribed!")
        for i, violation in enumerate(violations, 1):
            print(f"{i}. Edge {violation.edge_uuid[:8]}...")
            print(f"   Capacity: {violation.capacity_gbps:.1f} Gbps")
            print(f"   Total Demand: {violation.total_demand_gbps:.1f} Gbps")
            print(f"   Overage: {violation.overage:.1f} Gbps "
                  f"({(violation.overage / violation.capacity_gbps * 100):.1f}% over)")
    else:
        print("✓ No capacity violations detected")

    # 5. Specific Edge Utilization Analysis
    print("\n5. Analyze Specific Edge")
    print("-" * 60)
    if capacity_summary:
        edge_uuid = capacity_summary[0].uuid
        utilization = client.get_edge_utilization(edge_uuid)

        print(f"Edge: {utilization.uuid[:8]}...")
        print(f"  Capacity: {utilization.capacity_gbps:.1f} Gbps")
        print(f"  Total Demand: {utilization.total_demand_gbps:.1f} Gbps")
        print(f"  Free Capacity: {utilization.capacity_gbps - utilization.total_demand_gbps:.1f} Gbps")
        print(f"  Utilization: {utilization.utilization_pct:.1f}%")
        print(f"  Services Using Edge: {utilization.service_count}")

        # Get services using this edge
        services = client.get_services_by_edge(edge_uuid)
        print(f"\n  Services traversing this edge:")
        for svc in services[:5]:  # Show first 5
            print(f"    - {svc.name}: {svc.demand_gbps:.1f} Gbps "
                  f"({svc.hop_count} hops)")

    # 6. Utilization Distribution
    print("\n6. Utilization Distribution Analysis")
    print("-" * 60)
    if capacity_summary:
        buckets = {
            "0-20%": 0,
            "20-40%": 0,
            "40-60%": 0,
            "60-80%": 0,
            "80-100%": 0,
            ">100%": 0
        }

        for edge in capacity_summary:
            util = edge.utilization_pct
            if util < 20:
                buckets["0-20%"] += 1
            elif util < 40:
                buckets["20-40%"] += 1
            elif util < 60:
                buckets["40-60%"] += 1
            elif util < 80:
                buckets["60-80%"] += 1
            elif util <= 100:
                buckets["80-100%"] += 1
            else:
                buckets[">100%"] += 1

        print("Utilization Distribution:")
        for bucket, count in buckets.items():
            bar = "█" * (count // 5) if count > 0 else ""
            pct = (count / len(capacity_summary) * 100) if capacity_summary else 0
            print(f"  {bucket:>9}: {count:3d} edges ({pct:5.1f}%) {bar}")

    # 7. Node Capacity Analysis
    print("\n7. Node Capacity Analysis")
    print("-" * 60)
    nodes = client.get_nodes()

    # Sort by free capacity
    sorted_nodes = sorted(nodes, key=lambda n: n.free_capacity_gbps)

    print("Nodes with Lowest Free Capacity:")
    for node in sorted_nodes[:5]:
        used_pct = ((node.capacity_gbps - node.free_capacity_gbps) / node.capacity_gbps * 100)
        print(f"  {node.name:25s} "
              f"Free: {node.free_capacity_gbps:6.1f} Gbps / {node.capacity_gbps:6.1f} Gbps "
              f"({used_pct:5.1f}% used)")

    # 8. Filter Nodes by Capacity
    print("\n8. Filter Nodes by Capacity Requirements")
    print("-" * 60)

    # Find nodes with at least 50 Gbps free capacity
    high_capacity_nodes = client.get_nodes(min_free_capacity=50.0)
    print(f"Nodes with ≥50 Gbps free capacity: {len(high_capacity_nodes)}")

    # Find nodes with total capacity between 100-200 Gbps
    medium_capacity_nodes = client.get_nodes(
        min_total_capacity=100.0,
        max_total_capacity=200.0
    )
    print(f"Nodes with 100-200 Gbps total capacity: {len(medium_capacity_nodes)}")

    # 9. Vendor Capacity Analysis
    print("\n9. Vendor Capacity Analysis")
    print("-" * 60)
    vendor_stats = {}

    for node in nodes:
        if node.vendor not in vendor_stats:
            vendor_stats[node.vendor] = {
                "count": 0,
                "total_capacity": 0.0,
                "total_free": 0.0
            }
        vendor_stats[node.vendor]["count"] += 1
        vendor_stats[node.vendor]["total_capacity"] += node.capacity_gbps
        vendor_stats[node.vendor]["total_free"] += node.free_capacity_gbps

    print("Capacity by Vendor:")
    for vendor, stats in sorted(vendor_stats.items()):
        avg_util = ((stats["total_capacity"] - stats["total_free"]) /
                    stats["total_capacity"] * 100) if stats["total_capacity"] > 0 else 0
        print(f"  {vendor:15s}: {stats['count']:2d} nodes, "
              f"Total: {stats['total_capacity']:6.0f} Gbps, "
              f"Avg Util: {avg_util:5.1f}%")

    # 10. Monitoring Alert Simulation
    print("\n10. Monitoring Alert Simulation")
    print("-" * 60)
    alerts = []

    # Check for high utilization
    high_util = client.get_high_utilization_edges(threshold_pct=85.0)
    if high_util:
        alerts.append(f"⚠ {len(high_util)} edges have utilization ≥85%")

    # Check for violations
    violations = client.get_capacity_violations()
    if violations:
        alerts.append(f"🔴 {len(violations)} edges are oversubscribed")

    # Check for low free capacity nodes
    low_capacity_nodes = [n for n in nodes if n.free_capacity_gbps < 10.0]
    if low_capacity_nodes:
        alerts.append(f"⚠ {len(low_capacity_nodes)} nodes have <10 Gbps free capacity")

    if alerts:
        print("Active Alerts:")
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("✓ No alerts - All systems operating normally")

    print("\n" + "=" * 60)
    print("Capacity monitoring examples completed!")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    main()
