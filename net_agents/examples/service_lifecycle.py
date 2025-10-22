#!/usr/bin/env python3
"""
Service lifecycle management examples for Network Simulator Client.

This script demonstrates end-to-end service creation, management, and deletion.
"""
from datetime import datetime
from network_simulator_client import (
    NetworkSimulatorClient,
    ServiceCreate,
    RouteNotFoundError,
)


def main():
    """Demonstrate service lifecycle management."""

    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    print("=" * 60)
    print("Network Simulator Client - Service Lifecycle Examples")
    print("=" * 60)

    # 1. List Existing Services
    print("\n1. List Existing Services")
    print("-" * 60)
    services = client.get_services(limit=10)
    print(f"Found {len(services)} services (showing up to 10)")

    if services:
        for i, svc in enumerate(services[:5], 1):
            print(f"{i}. {svc.name}")
            print(f"   Demand: {svc.demand_gbps:.1f} Gbps, "
                  f"Hops: {svc.hop_count}, "
                  f"Distance: {svc.total_distance_km:.1f} km")

    # 2. Get Specific Service Details
    print("\n2. Get Specific Service Details")
    print("-" * 60)
    if services:
        service = client.get_service(services[0].uuid)
        print(f"Service: {service.name}")
        print(f"  UUID: {service.uuid}")
        print(f"  Source Node: {service.source_node_uuid[:8]}...")
        print(f"  Destination Node: {service.destination_node_uuid[:8]}...")
        print(f"  Demand: {service.demand_gbps:.1f} Gbps")
        print(f"  Routing Stage: {}")
        print(f"  Hop Count: {service.hop_count}")
        print(f"  Total Distance: {service.total_distance_km:.1f} km")
        print(f"  Path Nodes: {len(service.path_node_uuids)} nodes")
        print(f"  Path Edges: {len(service.path_edge_uuids)} edges")
        print(f"  Created: {service.created_at}")

    # 3. Get Services by Source Node
    print("\n3. Get Services by Source Node")
    print("-" * 60)
    if services:
        source_uuid = services[0].source_node_uuid
        node_services = client.get_services_by_node(source_uuid)
        print(f"Services originating from node {source_uuid[:8]}...: {len(node_services)}")
        for svc in node_services[:3]:
            print(f"  - {svc.name}: {svc.demand_gbps:.1f} Gbps")

    # 4. Get Services by Edge
    print("\n4. Get Services by Edge")
    print("-" * 60)
    if services and services[0].path_edge_uuids:
        edge_uuid = services[0].path_edge_uuids[0]
        edge_services = client.get_services_by_edge(edge_uuid)
        print(f"Services traversing edge {edge_uuid[:8]}...: {len(edge_services)}")

        # Calculate total demand on this edge
        total_demand = sum(svc.demand_gbps for svc in edge_services)
        print(f"  Total demand on edge: {total_demand:.1f} Gbps")

    # 5. Create New Service (Example workflow)
    print("\n5. Create New Service (Workflow Example)")
    print("-" * 60)
    print("Step-by-step service creation:")

    # Get nodes for source and destination
    nodes = client.get_nodes()
    if len(nodes) >= 2:
        source_node = nodes[0]
        dest_node = nodes[-1]

        print(f"  Source: {source_node.name}")
        print(f"  Destination: {dest_node.name}")

        # Compute route
        print(f"  Computing route...")
        try:
            route = client.compute_route(
                source_node_uuid=source_node.uuid,
                destination_node_uuid=dest_node.uuid,
                demand_gbps=5.0
            )
            print(f"  ✓ Route found: {route.hop_count} hops, {route.total_distance_km:.1f} km")

            # Example service creation (commented out to avoid modifying data)
            print("\n  Example code to create service:")
            print(f"""
    service_create = ServiceCreate(
        name="Example-Service-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        source_node_uuid="{source_node.uuid}",
        destination_node_uuid="{dest_node.uuid}",
        demand_gbps=5.0,
        
        path_node_uuids={route.path_node_uuids!r},
        path_edge_uuids={route.path_edge_uuids!r},
        service_timestamp="{datetime.utcnow().isoformat()}Z"
    )
    created_service = client.create_service(service_create)
    print(f"Created service: {{created_service.uuid}}")
            """)

        except RouteNotFoundError as e:
            print(f"  ✗ No route found: {e}")

    # 6. Service Impact Analysis
    print("\n6. Service Impact Analysis")
    print("-" * 60)
    if services:
        service = services[0]
        print(f"Analyzing service: {service.name}")

        # Check capacity impact on each edge in the path
        print(f"  Capacity impact on path edges:")
        total_impact = 0.0
        for i, edge_uuid in enumerate(service.path_edge_uuids, 1):
            try:
                util = client.get_edge_utilization(edge_uuid)
                impact_pct = (service.demand_gbps / util.capacity_gbps * 100)
                total_impact += impact_pct
                print(f"    Edge {i}: {impact_pct:.1f}% of capacity "
                      f"(Edge util: {util.utilization_pct:.1f}%)")
            except Exception:
                print(f"    Edge {i}: Could not retrieve utilization")

        avg_impact = total_impact / len(service.path_edge_uuids) if service.path_edge_uuids else 0
        print(f"  Average capacity impact: {avg_impact:.1f}%")

    # 7. Service Comparison
    print("\n7. Compare Multiple Services")
    print("-" * 60)
    if len(services) >= 3:
        print("Service Comparison:")
        print(f"{'Name':<30} {'Demand':>8} {'Hops':>5} {'Distance':>10}")
        print("-" * 60)

        for svc in services[:5]:
            print(f"{svc.name:<30} "
                  f"{svc.demand_gbps:>7.1f}G "
                  f"{svc.hop_count:>5} "
                  f"{svc.total_distance_km:>9.1f}km")

    # 8. Find Services with High Demand
    print("\n8. Find High-Demand Services")
    print("-" * 60)
    all_services = client.get_services(limit=1000)
    high_demand = sorted(
        [s for s in all_services if s.demand_gbps >= 10.0],
        key=lambda s: s.demand_gbps,
        reverse=True
    )

    print(f"Services with demand ≥10 Gbps: {len(high_demand)}")
    for svc in high_demand[:5]:
        print(f"  {svc.name}: {svc.demand_gbps:.1f} Gbps "
              f"({svc.hop_count} hops)")

    # 9. Delete Service (Example)
    print("\n9. Delete Service (Example - Commented Out)")
    print("-" * 60)
    print("Example code:")
    print("""
    # Delete a service and free up capacity
    if services:
        service_uuid = services[0].uuid
        client.delete_service(service_uuid)
        print(f"Deleted service: {service_uuid}")
        print("Capacity on path edges has been freed")
    """)

    # 11. Service Path Validation
    print("\n11. Service Path Validation")
    print("-" * 60)
    if services:
        service = services[0]
        print(f"Validating service: {service.name}")

        validation = client.validate_path(
            path_node_uuids=service.path_node_uuids,
            path_edge_uuids=service.path_edge_uuids,
            demand_gbps=service.demand_gbps
        )

        if validation["valid"]:
            print("  ✓ Service path is valid")
            print(f"    Distance: {validation['total_distance_km']:.1f} km")
            print(f"    Min Available Capacity: {validation['min_available_capacity']:.1f} Gbps")
        else:
            print("  ✗ Service path has issues:")
            for error in validation["errors"]:
                print(f"    - {error}")

    # 12. Service Lifecycle Summary
    print("\n12. Service Lifecycle Summary")
    print("-" * 60)
    print("Complete service lifecycle:")
    print("  1. Identify source and destination nodes")
    print("  2. Compute route using A* algorithm")
    print("  3. Validate route has sufficient capacity")
    print("  4. Create service with computed path")
    print("  5. Monitor service impact on network")
    print("  6. Analyze service performance")
    print("  7. Delete service when no longer needed")

    print("\n" + "=" * 60)
    print("Service lifecycle examples completed!")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    main()
