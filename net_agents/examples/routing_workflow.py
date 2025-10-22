#!/usr/bin/env python3
"""
Routing workflow examples for Network Simulator Client.

This script demonstrates A* routing computation and route analysis.
"""
from network_simulator_client import (
    NetworkSimulatorClient,
    RouteNotFoundError,
)


def main():
    """Demonstrate routing workflows."""

    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    print("=" * 60)
    print("Network Simulator Client - Routing Workflow Examples")
    print("=" * 60)

    # 1. Get sample nodes for routing
    print("\n1. Get Sample Nodes for Routing")
    print("-" * 60)
    nodes = client.get_nodes()
    if len(nodes) < 2:
        print("Error: Need at least 2 nodes for routing examples")
        return

    print(f"Total nodes available: {len(nodes)}")
    source_node = nodes[0]
    dest_node = nodes[-1]  # Pick a distant node
    print(f"Source: {source_node.name} (UUID: {source_node.uuid[:8]}...)")
    print(f"Destination: {dest_node.name} (UUID: {dest_node.uuid[:8]}...)")

    # 2. Compute Route with Default Demand
    print("\n2. Compute Route with Default Demand (5.0 Gbps)")
    print("-" * 60)
    try:
        route = client.compute_route(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid
        )
        print(f"Route found successfully!")
        print(f"  Total Distance: {route.total_distance_km:.2f} km")
        print(f"  Hop Count: {route.hop_count}")
        print(f"  Min Available Capacity: {route.min_available_capacity:.2f} Gbps")
        print(f"  Computation Time: {route.computation_time_ms:.2f} ms")
        print(f"  Path Nodes: {len(route.path_node_uuids)} nodes")
        print(f"  Path Edges: {len(route.path_edge_uuids)} edges")
    except RouteNotFoundError as e:
        print(f"No route found: {e}")

    # 3. Compute Route with Custom Demand
    print("\n3. Compute Route with Custom Demand (10.0 Gbps)")
    print("-" * 60)
    try:
        route = client.compute_route(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid,
            demand_gbps=10.0
        )
        print(f"Route found successfully!")
        print(f"  Total Distance: {route.total_distance_km:.2f} km")
        print(f"  Hop Count: {route.hop_count}")
        print(f"  Min Available Capacity: {route.min_available_capacity:.2f} Gbps")
        print(f"  Bottleneck Check: {'OK' if route.min_available_capacity >= 10.0 else 'WARNING'}")
    except RouteNotFoundError as e:
        print(f"No route found: {e}")

    # 4. Compute Route Using GET Method
    print("\n4. Compute Route Using GET Method")
    print("-" * 60)
    try:
        route = client.compute_route_get(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid,
            demand_gbps=5.0
        )
        print(f"Route found via GET method!")
        print(f"  Hop Count: {route.hop_count}")
        print(f"  Total Distance: {route.total_distance_km:.2f} km")
    except RouteNotFoundError as e:
        print(f"No route found: {e}")

    # 5. Analyze Route Path
    print("\n5. Analyze Route Path Details")
    print("-" * 60)
    try:
        route = client.compute_route(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid,
            demand_gbps=5.0
        )

        print(f"Path Analysis:")
        print(f"  Source Node: {source_node.name}")
        for i, node_uuid in enumerate(route.path_node_uuids[1:-1], 1):
            try:
                node = client.get_node(node_uuid)
                print(f"  Intermediate Node {i}: {node.name} (Free: {node.free_capacity_gbps:.1f} Gbps)")
            except Exception:
                print(f"  Intermediate Node {i}: {node_uuid[:8]}...")
        print(f"  Destination Node: {dest_node.name}")

        print(f"\nEdge Utilization Along Path:")
        for i, edge_uuid in enumerate(route.path_edge_uuids, 1):
            try:
                utilization = client.get_edge_utilization(edge_uuid)
                print(f"  Edge {i}: {utilization.utilization_pct:.1f}% utilized "
                      f"({utilization.total_demand_gbps:.1f}/{utilization.capacity_gbps:.1f} Gbps)")
            except Exception:
                print(f"  Edge {i}: {edge_uuid[:8]}...")

    except RouteNotFoundError as e:
        print(f"No route found: {e}")

    # 6. Test High-Demand Route
    print("\n6. Test High-Demand Route (100 Gbps)")
    print("-" * 60)
    try:
        route = client.compute_route(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid,
            demand_gbps=100.0
        )
        print(f"Route found for high demand!")
        print(f"  Min Available Capacity: {route.min_available_capacity:.2f} Gbps")
        if route.min_available_capacity >= 100.0:
            print(f"  ✓ Path can support 100 Gbps demand")
        else:
            print(f"  ⚠ Path may be insufficient (only {route.min_available_capacity:.2f} Gbps available)")
    except RouteNotFoundError as e:
        print(f"No route found for high demand: {e}")

    # 7. Compare Multiple Routes
    print("\n7. Compare Routes Between Different Node Pairs")
    print("-" * 60)
    if len(nodes) >= 3:
        pairs = [
            (nodes[0], nodes[1]),
            (nodes[0], nodes[2]),
            (nodes[1], nodes[2])
        ]

        for src, dst in pairs:
            try:
                route = client.compute_route(
                    source_node_uuid=src.uuid,
                    destination_node_uuid=dst.uuid,
                    demand_gbps=5.0
                )
                print(f"{src.name} → {dst.name}:")
                print(f"  Distance: {route.total_distance_km:.2f} km, "
                      f"Hops: {route.hop_count}, "
                      f"Min Capacity: {route.min_available_capacity:.1f} Gbps")
            except RouteNotFoundError:
                print(f"{src.name} → {dst.name}: No route found")

    # 8. Validate Custom Path
    print("\n8. Validate Custom Path")
    print("-" * 60)
    try:
        route = client.compute_route(
            source_node_uuid=source_node.uuid,
            destination_node_uuid=dest_node.uuid,
            demand_gbps=5.0
        )

        # Use the validate_path helper
        validation = client.validate_path(
            path_node_uuids=route.path_node_uuids,
            path_edge_uuids=route.path_edge_uuids,
            demand_gbps=5.0
        )

        if validation["valid"]:
            print("✓ Path is valid")
            print(f"  Total Distance: {validation['total_distance_km']:.2f} km")
            print(f"  Min Available Capacity: {validation['min_available_capacity']:.2f} Gbps")
        else:
            print("✗ Path is invalid")
            for error in validation["errors"]:
                print(f"  - {error}")

    except RouteNotFoundError as e:
        print(f"No route found: {e}")

    # 9. Find Routes from Node by Geographic Filtering
    print("\n9. Find Nearby Nodes for Routing")
    print("-" * 60)
    if nodes:
        reference_node = nodes[0]
        nearby_nodes = client.get_nodes(
            latitude=reference_node.latitude,
            longitude=reference_node.longitude,
            max_distance_km=500.0
        )
        print(f"Found {len(nearby_nodes)} nodes within 500 km of {reference_node.name}")
        if len(nearby_nodes) > 1:
            # Try routing to a nearby node
            target = nearby_nodes[1]
            try:
                route = client.compute_route(
                    source_node_uuid=reference_node.uuid,
                    destination_node_uuid=target.uuid,
                    demand_gbps=5.0
                )
                print(f"Route to nearby node {target.name}:")
                print(f"  Distance: {route.total_distance_km:.2f} km")
                print(f"  Hops: {route.hop_count}")
            except RouteNotFoundError:
                print(f"No route found to {target.name}")

    print("\n" + "=" * 60)
    print("Routing workflow examples completed!")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    main()
