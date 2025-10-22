"""
Demonstration of database query capabilities.
Shows powerful queries enabled by the SQLite migration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.database_manager import NetworkDatabase


def demo_queries(db: NetworkDatabase):
    """Demonstrate various database queries."""
    cursor = db.conn.cursor()

    print("=" * 70)
    print("DATABASE QUERY DEMONSTRATIONS")
    print("=" * 70)

    # Query 1: Top 10 highest capacity nodes
    print("\n[QUERY 1] Top 10 Highest Capacity Nodes")
    print("-" * 70)
    cursor.execute("""
        SELECT name, vendor, capacity_gbps
        FROM nodes
        ORDER BY capacity_gbps DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:30s} ({row[1]:15s}) - {row[2]:7.0f} Gbps")

    # Query 2: Most utilized edges
    print("\n[QUERY 2] Top 10 Most Utilized Edges")
    print("-" * 70)
    cursor.execute("""
        SELECT edge_name, capacity_gbps, total_demand_gbps, utilization_pct, service_count
        FROM capacity_summary
        WHERE service_count > 0
        ORDER BY utilization_pct DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:50s} {row[3]:5.1f}% ({row[4]:2d} services)")

    # Query 3: Longest distance services
    print("\n[QUERY 3] Top 5 Longest Distance Services")
    print("-" * 70)
    cursor.execute("""
        SELECT name, hop_count, total_distance_km
        FROM services
        ORDER BY total_distance_km DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        service_name = row[0].replace("Service ", "")
        print(f"  {service_name:45s} {row[1]:2d} hops, {row[2]:7.2f} km")

    # Query 4: Services by routing stage
    print("\n[QUERY 4] Service Distribution by Routing Stage")
    print("-" * 70)
    cursor.execute("""
        SELECT routing_stage,
               COUNT(*) as count,
               AVG(hop_count) as avg_hops,
               AVG(total_distance_km) as avg_distance_km
        FROM services
        GROUP BY routing_stage
        ORDER BY routing_stage
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:10s}: {row[1]:3d} services, avg {row[2]:.2f} hops, avg {row[3]:.2f} km")

    # Query 5: Find a specific edge's services
    print("\n[QUERY 5] Find Services Using NYC-Manhattan ↔ Philadelphia Edge")
    print("-" * 70)

    # First get NYC and Philadelphia UUIDs
    nyc = db.get_node_by_name("NYC-Manhattan")
    philly = db.get_node_by_name("Philadelphia-Center")

    if nyc and philly:
        edge = db.get_edge_by_endpoints(nyc['uuid'], philly['uuid'])
        if edge:
            services = db.get_services_using_edge(edge['uuid'])
            print(f"  Edge capacity: {edge['capacity_gbps']:.2f} Gbps")
            print(f"  Services using this edge: {len(services)}")
            for svc in services[:5]:
                print(f"    • {svc['name']} ({svc['hop_count']} hops)")
            if len(services) > 5:
                print(f"    ... and {len(services) - 5} more")

    # Query 6: Node degree distribution
    print("\n[QUERY 6] Node Degree Distribution")
    print("-" * 70)
    cursor.execute("""
        WITH node_degrees AS (
            SELECT
                n.name,
                n.capacity_gbps,
                (SELECT COUNT(*) FROM edges e
                 WHERE e.node1_uuid = n.uuid OR e.node2_uuid = n.uuid) as degree
            FROM nodes n
        )
        SELECT
            CASE
                WHEN degree <= 3 THEN '1-3'
                WHEN degree <= 6 THEN '4-6'
                WHEN degree <= 9 THEN '7-9'
                ELSE '10+'
            END as degree_range,
            COUNT(*) as node_count,
            AVG(capacity_gbps) as avg_capacity
        FROM node_degrees
        GROUP BY degree_range
        ORDER BY degree_range
    """)
    for row in cursor.fetchall():
        print(f"  Degree {row[0]:5s}: {row[1]:2d} nodes, avg capacity {row[2]:7.0f} Gbps")

    # Query 7: Busiest nodes (most services)
    print("\n[QUERY 7] Top 5 Busiest Nodes (Most Services as Endpoint)")
    print("-" * 70)
    cursor.execute("""
        WITH node_service_counts AS (
            SELECT
                n.uuid,
                n.name,
                COUNT(*) as service_count
            FROM nodes n
            JOIN services s ON n.uuid = s.source_node_uuid OR n.uuid = s.destination_node_uuid
            GROUP BY n.uuid
        )
        SELECT name, service_count
        FROM node_service_counts
        ORDER BY service_count DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:30s} {row[1]:3d} services")

    # Query 8: Timeline distribution
    print("\n[QUERY 8] Service Timeline Distribution")
    print("-" * 70)
    cursor.execute("""
        SELECT
            SUBSTR(service_timestamp, 1, 4) as year,
            COUNT(*) as count
        FROM services
        GROUP BY year
        ORDER BY year
    """)
    for row in cursor.fetchall():
        bar = "█" * (row[1] // 2)
        print(f"  {row[0]}: {bar} ({row[1]} services)")

    # Query 9: Path length distribution
    print("\n[QUERY 9] Path Length (Hop Count) Distribution")
    print("-" * 70)
    cursor.execute("""
        SELECT hop_count, COUNT(*) as count
        FROM services
        GROUP BY hop_count
        ORDER BY hop_count
    """)
    for row in cursor.fetchall():
        bar = "█" * row[1]
        print(f"  {row[0]:2d} hops: {bar} ({row[1]} services)")

    # Query 10: Capacity utilization summary
    print("\n[QUERY 10] Overall Capacity Utilization Summary")
    print("-" * 70)
    cursor.execute("""
        SELECT
            SUM(e.capacity_gbps) as total_capacity,
            SUM(COALESCE(cu.total_demand_gbps, 0)) as total_demand,
            (SUM(COALESCE(cu.total_demand_gbps, 0)) / SUM(e.capacity_gbps) * 100) as utilization_pct
        FROM edges e
        LEFT JOIN capacity_utilization cu ON e.uuid = cu.edge_uuid
    """)
    row = cursor.fetchone()
    print(f"  Total edge capacity:    {row[0]:10,.2f} Gbps")
    print(f"  Total demand allocated: {row[1]:10,.2f} Gbps")
    print(f"  Overall utilization:    {row[2]:10.2f}%")

    cursor.close()


def demo_advanced_queries(db: NetworkDatabase):
    """Demonstrate advanced analytical queries."""
    cursor = db.conn.cursor()

    print("\n" + "=" * 70)
    print("ADVANCED ANALYTICS QUERIES")
    print("=" * 70)

    # Query 11: Find multi-hop services through specific node
    print("\n[QUERY 11] Services Routing Through Chicago-Loop (Transit Node)")
    print("-" * 70)
    chicago = db.get_node_by_name("Chicago-Loop")
    if chicago:
        cursor.execute("""
            SELECT DISTINCT s.name, s.hop_count, s.total_distance_km
            FROM services s
            JOIN service_path_nodes spn ON s.uuid = spn.service_uuid
            WHERE spn.node_uuid = ?
              AND spn.sequence_order > 0
              AND spn.sequence_order < s.hop_count
            ORDER BY s.hop_count DESC
            LIMIT 5
        """, (chicago['uuid'],))

        results = cursor.fetchall()
        print(f"  Found {len(results)} services transiting through Chicago-Loop:")
        for row in results:
            service_name = row[0].replace("Service ", "")
            print(f"    {service_name:40s} {row[1]:2d} hops, {row[2]:6.2f} km")

    # Query 12: Edge utilization by vendor
    print("\n[QUERY 12] Average Edge Utilization by Vendor")
    print("-" * 70)
    cursor.execute("""
        SELECT
            n1.vendor,
            COUNT(DISTINCT e.uuid) as edge_count,
            AVG(COALESCE(cs.utilization_pct, 0)) as avg_utilization
        FROM nodes n1
        JOIN edges e ON n1.uuid = e.node1_uuid
        JOIN nodes n2 ON e.node2_uuid = n2.uuid
        LEFT JOIN capacity_summary cs ON e.uuid = cs.edge_uuid
        WHERE n1.vendor = n2.vendor
        GROUP BY n1.vendor
        ORDER BY avg_utilization DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:15s}: {row[1]:3d} edges, avg {row[2]:5.2f}% utilized")

    # Query 13: Correlation between distance and hop count
    print("\n[QUERY 13] Distance vs Hop Count Correlation")
    print("-" * 70)
    cursor.execute("""
        SELECT
            hop_count,
            COUNT(*) as service_count,
            AVG(total_distance_km) as avg_distance,
            MIN(total_distance_km) as min_distance,
            MAX(total_distance_km) as max_distance
        FROM services
        GROUP BY hop_count
        HAVING COUNT(*) >= 2
        ORDER BY hop_count
    """)
    print(f"  {'Hops':<6} {'Count':<7} {'Avg Dist (km)':<15} {'Range (km)':<20}")
    print(f"  {'-'*6} {'-'*7} {'-'*15} {'-'*20}")
    for row in cursor.fetchall():
        print(f"  {row[0]:<6d} {row[1]:<7d} {row[2]:<15.2f} {row[3]:.2f} - {row[4]:.2f}")

    cursor.close()


def main():
    """Run all demonstrations."""
    db_path = Path("data/network.db")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run 'python migrations/import_existing_data.py' first.")
        sys.exit(1)

    db = NetworkDatabase(str(db_path))

    demo_queries(db)
    demo_advanced_queries(db)

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nThe database enables powerful queries that were difficult with CSV/JSON:")
    print("  • Instant edge utilization lookups")
    print("  • Complex path analysis")
    print("  • Vendor-based analytics")
    print("  • Timeline queries")
    print("  • Referential integrity validation")

    db.close()


if __name__ == "__main__":
    main()
