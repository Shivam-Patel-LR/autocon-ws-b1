#!/usr/bin/env python3
"""
Basic usage examples for Network Simulator Client.

This script demonstrates fundamental CRUD operations for nodes and edges.
"""
from network_simulator_client import (
    NetworkSimulatorClient,
    NodeCreate,
    NodeUpdate,
    EdgeCreate,
    NodeNotFoundError,
)


def main():
    """Demonstrate basic usage of the Network Simulator Client."""

    # Initialize client (adjust base_url if needed)
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    print("=" * 60)
    print("Network Simulator Client - Basic Usage Examples")
    print("=" * 60)

    # 1. Health Check
    print("\n1. Health Check")
    print("-" * 60)
    try:
        health = client.health_check()
        print(f"API Status: {health.status}")
        print(f"Database Status: {health.database}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # 2. Get Database Statistics
    print("\n2. Database Statistics")
    print("-" * 60)
    stats = client.get_database_stats()
    print(f"Total Nodes: {stats.nodes}")
    print(f"Total Edges: {stats.edges}")
    print(f"Total Services: {stats.services}")

    # 3. List All Nodes
    print("\n3. List All Nodes")
    print("-" * 60)
    nodes = client.get_nodes()
    print(f"Found {len(nodes)} nodes")
    if nodes:
        for i, node in enumerate(nodes[:3], 1):  # Show first 3
            print(f"  {i}. {node.name} ({node.vendor}) - "
                  f"Capacity: {node.capacity_gbps} Gbps, "
                  f"Free: {node.free_capacity_gbps} Gbps")

    # 4. Filter Nodes by Vendor
    print("\n4. Filter Nodes by Vendor")
    print("-" * 60)
    if nodes:
        # Get unique vendors
        vendors = list(set(node.vendor for node in nodes))
        if vendors:
            target_vendor = vendors[0]
            vendor_nodes = client.get_nodes(vendor=target_vendor)
            print(f"Nodes from {target_vendor}: {len(vendor_nodes)}")

    # 5. Search Nodes by Name
    print("\n5. Search Nodes by Name")
    print("-" * 60)
    if nodes:
        search_term = nodes[0].name[:3]  # First 3 chars of first node
        results = client.search_nodes_by_name(search_term)
        print(f"Search for '{search_term}': {len(results)} results")
        for node in results[:3]:
            print(f"  - {node.name}")

    # 6. Get Specific Node
    print("\n6. Get Specific Node")
    print("-" * 60)
    if nodes:
        node_uuid = nodes[0].uuid
        node = client.get_node(node_uuid)
        print(f"Node UUID: {node.uuid}")
        print(f"Name: {node.name}")
        print(f"Location: ({node.latitude}, {node.longitude})")
        print(f"Vendor: {node.vendor}")
        print(f"Capacity: {node.capacity_gbps} Gbps")
        print(f"Free Capacity: {node.free_capacity_gbps} Gbps")

    # 7. Create a New Node (Example - commented out to avoid data changes)
    print("\n7. Create New Node (Example - Commented Out)")
    print("-" * 60)
    print("Example code:")
    print("""
    new_node = NodeCreate(
        name="Example-Node-01",
        latitude=40.7128,
        longitude=-74.0060,
        vendor="Cisco",
        capacity_gbps=100.0
    )
    created_node = client.create_node(new_node)
    print(f"Created node: {created_node.name} with UUID: {created_node.uuid}")
    """)

    # 8. Update Node (Example - commented out)
    print("\n8. Update Node (Example - Commented Out)")
    print("-" * 60)
    print("Example code:")
    print("""
    node_update = NodeUpdate(capacity_gbps=200.0, vendor="Juniper")
    updated_node = client.update_node(node_uuid, node_update)
    print(f"Updated node capacity: {updated_node.capacity_gbps} Gbps")
    """)

    # 9. List All Edges
    print("\n9. List All Edges")
    print("-" * 60)
    edges = client.get_edges()
    print(f"Found {len(edges)} edges")
    if edges:
        for i, edge in enumerate(edges[:3], 1):  # Show first 3
            print(f"  {i}. Edge {edge.uuid[:8]}... "
                  f"Capacity: {edge.capacity_gbps} Gbps")

    # 10. Get Edge by Endpoints
    print("\n10. Get Edge by Endpoints")
    print("-" * 60)
    if edges:
        edge = edges[0]
        found_edge = client.get_edge_by_endpoints(
            edge.node1_uuid,
            edge.node2_uuid
        )
        print(f"Found edge: {found_edge.uuid}")
        print(f"Connects: {found_edge.node1_uuid[:8]}... to {found_edge.node2_uuid[:8]}...")
        print(f"Capacity: {found_edge.capacity_gbps} Gbps")

    # 11. Create Edge (Example - commented out)
    print("\n11. Create Edge (Example - Commented Out)")
    print("-" * 60)
    print("Example code:")
    print("""
    if len(nodes) >= 2:
        new_edge = EdgeCreate(
            node1_uuid=nodes[0].uuid,
            node2_uuid=nodes[1].uuid,
            capacity_gbps=50.0
        )
        created_edge = client.create_edge(new_edge)
        print(f"Created edge: {created_edge.uuid}")
    """)

    # 12. Error Handling Example
    print("\n12. Error Handling Example")
    print("-" * 60)
    try:
        # Try to get a non-existent node
        client.get_node("non-existent-uuid")
    except NodeNotFoundError as e:
        print(f"Caught expected exception: {e}")
        print(f"Status code: {e.status_code}")

    # 13. Using Context Manager
    print("\n13. Using Context Manager (Recommended)")
    print("-" * 60)
    print("Example code:")
    print("""
    with NetworkSimulatorClient(base_url="http://localhost:8003") as client:
        nodes = client.get_nodes()
        print(f"Found {len(nodes)} nodes")
        # Client automatically closes when exiting context
    """)

    print("\n" + "=" * 60)
    print("Basic usage examples completed!")
    print("=" * 60)

    # Clean up
    client.close()


if __name__ == "__main__":
    main()
