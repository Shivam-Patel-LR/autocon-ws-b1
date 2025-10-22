#!/usr/bin/env python3
"""
Network Planning Agent - Exercise 2

A simple testing agent with comprehensive tools for interacting with the
Network Simulator API. This agent validates the plumbing and functionality
of all network endpoints.
"""
import asyncio
import json
import textwrap
from math import radians, sin, cos, sqrt, atan2
from colorama import Fore, Style, init as colorama_init
from agents import (
    Agent,
    OpenAIResponsesModel,
    set_tracing_disabled,
    function_tool,
    Runner,
)
from dotenv import load_dotenv
from config import llm_client, GENERATIVE_MODEL
from network_simulator_client import NetworkSimulatorClient

# Load environment variables
load_dotenv()


@function_tool
async def get_nodes_by_name(name_substring: str) -> str:
    """
    Search for network nodes by name using case-insensitive substring matching.

    This tool searches the network topology for nodes whose names contain the
    specified substring. The search is case-insensitive and returns all matching
    nodes with their complete details including geographic location, capacity
    information, and unique identifiers.

    Parameters
    ----------
    name_substring : str
        The substring to search for in node names. Case-insensitive.
        Examples: "Albany", "boston", "NYC", "miami"

    Returns
    -------
    List[Dict[str, Any]]
        A list of matching nodes, where each node is a dictionary containing:

        - uuid (str): Unique identifier for the node (UUID format)
        - name (str): Human-readable name of the node (e.g., "Albany-NY")
        - latitude (float): Latitude coordinate in degrees (-90 to 90)
        - longitude (float): Longitude coordinate in degrees (-180 to 180)
        - vendor (str): Network equipment vendor (e.g., "Cisco", "Juniper")
        - capacity_gbps (float): Total node capacity in Gigabits per second
        - free_capacity_gbps (float): Available (unused) capacity in Gbps
        - location_string (str): Formatted location string for display

    Raises
    ------
    APIConnectionError
        If unable to connect to the Network Simulator API
    APITimeoutError
        If the API request times out

    Examples
    --------
    Search for nodes in Albany:
        >>> get_nodes_by_name("Albany")
        [{"uuid": "abc-123", "name": "Albany-NY", "capacity_gbps": 100.0, ...}]

    Search for Boston nodes:
        >>> get_nodes_by_name("boston")
        [{"uuid": "def-456", "name": "Boston-MA", "capacity_gbps": 150.0, ...}]

    Notes
    -----
    - The network contains approximately 48 nodes distributed across the eastern US
    - Search is performed server-side for efficiency
    - Empty list is returned if no nodes match the search criteria
    - All nodes have bidirectional connections (edges) to neighboring nodes
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        nodes = client.search_nodes_by_name(name_substring)

        result = []
        for node in nodes:
            result.append(
                {
                    "uuid": node.uuid,
                    "name": node.name,
                    "latitude": node.latitude,
                    "longitude": node.longitude,
                    "vendor": node.vendor,
                    "capacity_gbps": node.capacity_gbps,
                    "free_capacity_gbps": node.free_capacity_gbps,
                    "location_string": f"({node.latitude:.4f}, {node.longitude:.4f})",
                }
            )

        return json.dumps(result)

    except Exception as e:
        return json.dumps([{"error": str(e), "search_term": name_substring}])
    finally:
        client.close()


@function_tool
async def get_nodes_by_location(
    latitude: float, longitude: float, max_distance_km: float
) -> str:
    """
    Find network nodes within a specified geographic radius using haversine distance.

    This tool performs a geographic radius search to find all network nodes within
    a specified distance from a given coordinate point. The distance is calculated
    using the haversine formula, which accounts for the Earth's spherical shape and
    provides accurate great-circle distances.

    Parameters
    ----------
    latitude : float
        Latitude of the center point in decimal degrees (-90 to 90).
        Positive values are North, negative values are South.
        Example: 40.7128 for New York City

    longitude : float
        Longitude of the center point in decimal degrees (-180 to 180).
        Positive values are East, negative values are West.
        Example: -74.0060 for New York City

    max_distance_km : float
        Maximum distance from the center point in kilometers.
        Only nodes within this radius will be returned.
        Must be a positive value.
        Example: 100.0 for nodes within 100km radius

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the search results and metadata:

        - center_latitude (float): Echo of the search center latitude
        - center_longitude (float): Echo of the search center longitude
        - radius_km (float): Echo of the search radius
        - node_count (int): Number of nodes found within the radius
        - nodes (List[Dict]): List of nodes found, each containing:
            - uuid (str): Unique identifier for the node
            - name (str): Human-readable name of the node
            - latitude (float): Node's latitude coordinate
            - longitude (float): Node's longitude coordinate
            - vendor (str): Network equipment vendor
            - capacity_gbps (float): Total node capacity in Gbps
            - free_capacity_gbps (float): Available capacity in Gbps
            - distance_km (float): Calculated distance from center point

    Raises
    ------
    ValidationError
        If latitude, longitude, or max_distance_km are out of valid ranges
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Find nodes near New York City (within 50km):
        >>> get_nodes_by_location(40.7128, -74.0060, 50.0)
        {"node_count": 3, "nodes": [...]}

    Find nodes near Boston (within 100km):
        >>> get_nodes_by_location(42.3601, -71.0589, 100.0)
        {"node_count": 5, "nodes": [...]}

    Notes
    -----
    - Distance calculation uses the haversine formula for spherical geometry
    - The network spans the eastern United States (roughly -90 to -70 longitude)
    - Typical node density varies by region (higher in metropolitan areas)
    - Search is performed server-side for efficiency with large networks
    - Results are not sorted by distance; sort client-side if needed
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        nodes = client.get_nodes(
            latitude=latitude, longitude=longitude, max_distance_km=max_distance_km
        )

        result_nodes = []
        for node in nodes:
            # Calculate distance using haversine (approximation for display)

            lat1, lon1 = radians(latitude), radians(longitude)
            lat2, lon2 = radians(node.latitude), radians(node.longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance_km = 6371.0 * c  # Earth's radius in km

            result_nodes.append(
                {
                    "uuid": node.uuid,
                    "name": node.name,
                    "latitude": node.latitude,
                    "longitude": node.longitude,
                    "vendor": node.vendor,
                    "capacity_gbps": node.capacity_gbps,
                    "free_capacity_gbps": node.free_capacity_gbps,
                    "distance_km": round(distance_km, 2),
                }
            )

        return json.dumps(
            {
                "center_latitude": latitude,
                "center_longitude": longitude,
                "radius_km": max_distance_km,
                "node_count": len(result_nodes),
                "nodes": result_nodes,
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "center_latitude": latitude,
                "center_longitude": longitude,
                "radius_km": max_distance_km,
            }
        )
    finally:
        client.close()


@function_tool
async def get_node_services(node_uuid: str) -> str:
    """
    Retrieve all services originating from a specific network node.

    This tool queries the Network Simulator to find all services (network paths with
    allocated bandwidth) that originate from the specified node. Services represent
    provisioned network connections with source, destination, bandwidth demand, and
    the specific path (sequence of nodes and edges) used to route the traffic.

    Parameters
    ----------
    node_uuid : str
        The unique identifier (UUID) of the source node to query.
        Must be a valid UUID of an existing node in the network.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    Returns
    -------
    Dict[str, Any]
        A dictionary containing service information and metadata:

        - node_uuid (str): Echo of the queried node UUID
        - service_count (int): Number of services originating from this node
        - services (List[Dict]): List of services, each containing:
            - uuid (str): Unique identifier for the service
            - name (str): Human-readable service name
            - source_node_uuid (str): UUID of the source node (same as input)
            - destination_node_uuid (str): UUID of the destination node
            - demand_gbps (float): Bandwidth demand in Gigabits per second
            - hop_count (int): Number of hops (edges) in the service path
            - total_distance_km (float): Total geographic distance of the path
            - routing_stage (str): Routing stage identifier ("stage_a" or "stage_b")
            - path_node_uuids (List[str]): Ordered list of node UUIDs in the path
            - path_edge_uuids (List[str]): Ordered list of edge UUIDs in the path
            - service_timestamp (str): ISO 8601 timestamp when service was created

        If an error occurs:
        - error (str): Error message describing what went wrong
        - node_uuid (str): Echo of the queried node UUID

    Raises
    ------
    NodeNotFoundError
        If the specified node UUID does not exist in the network
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Get services from a specific node:
        >>> get_node_services("550e8400-e29b-41d4-a716-446655440000")
        {"service_count": 5, "services": [...]}

    Node with no services:
        >>> get_node_services("some-node-uuid")
        {"service_count": 0, "services": []}

    Notes
    -----
    - Only returns services where the queried node is the SOURCE (origin)
    - Services passing through the node but not originating there are NOT included
    - The network typically has 100+ services provisioned across all nodes
    - Each service reserves bandwidth (demand_gbps) on all edges in its path
    - Path validation ensures all nodes and edges in the path actually exist
    - Services are created using the A* pathfinding algorithm with capacity constraints
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        services = client.get_services_by_node(node_uuid)

        result_services = []
        for service in services:
            result_services.append(
                {
                    "uuid": service.uuid,
                    "name": service.name,
                    "source_node_uuid": service.source_node_uuid,
                    "destination_node_uuid": service.destination_node_uuid,
                    "demand_gbps": service.demand_gbps,
                    "hop_count": service.hop_count,
                    "total_distance_km": service.total_distance_km,
                    "path_node_uuids": service.path_node_uuids,
                    "path_edge_uuids": service.path_edge_uuids,
                    "service_timestamp": service.service_timestamp,
                }
            )

        return json.dumps(
            {
                "node_uuid": node_uuid,
                "service_count": len(result_services),
                "services": result_services,
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "node_uuid": node_uuid,
            }
        )
    finally:
        client.close()


@function_tool
async def get_edge_by_uuid(edge_uuid: str) -> str:
    """
    Retrieve detailed information about a specific network edge (connection) by its UUID.

    This tool fetches complete details for a single edge using its unique identifier.
    Edges represent bidirectional connections between two nodes with a specific capacity.
    Use this when you have an edge UUID from a route computation or service query and
    need to get detailed information about that connection, including its endpoints
    and capacity.

    Parameters
    ----------
    edge_uuid : str
        The unique identifier (UUID) of the edge to retrieve.
        Must be a valid UUID of an existing edge in the network.
        Example: "7c9e6679-7425-40de-944b-e07fc1f90ae7"

    Returns
    -------
    Dict[str, Any]
        A dictionary containing complete edge information:

        On Success:
        - uuid (str): Unique identifier for the edge
        - node1_uuid (str): UUID of the first endpoint node
        - node2_uuid (str): UUID of the second endpoint node
        - capacity_gbps (float): Total edge capacity in Gigabits per second
        - created_at (str): ISO 8601 timestamp when edge was created
        - updated_at (str): ISO 8601 timestamp of last modification

        On Failure:
        - error (str): Error message describing what went wrong
        - edge_uuid (str): Echo of the requested edge UUID

    Raises
    ------
    EdgeNotFoundError
        If the specified edge UUID does not exist in the network
    APIConnectionError
        If unable to connect to the Network Simulator API
    APITimeoutError
        If the API request times out

    Examples
    --------
    Get details for a specific edge:
        >>> get_edge_by_uuid("7c9e6679-7425-40de-944b-e07fc1f90ae7")
        {"uuid": "7c9e6679...", "node1_uuid": "550e8400...", "capacity_gbps": 50.0, ...}

    Edge not found:
        >>> get_edge_by_uuid("invalid-uuid")
        {"error": "Edge not found", "edge_uuid": "invalid-uuid"}

    Notes
    -----
    - Edges are bidirectional; node1 and node2 order is arbitrary
    - This is useful when you have an edge UUID from a route path_edge_uuids list
    - The network contains approximately 200 bidirectional edges
    - Edge capacity represents the maximum bandwidth available for services
    - To see how much capacity is actually in use, combine with capacity/utilization endpoints
    - Use get_node_by_uuid() to get details about the endpoint nodes
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        edge = client.get_edge(edge_uuid)

        return json.dumps(
            {
                "uuid": edge.uuid,
                "node1_uuid": edge.node1_uuid,
                "node2_uuid": edge.node2_uuid,
                "capacity_gbps": edge.capacity_gbps,
                "created_at": edge.created_at,
                "updated_at": edge.updated_at,
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e), "edge_uuid": edge_uuid})
    finally:
        client.close()


@function_tool
async def get_edge_by_endpoints(node1_uuid: str, node2_uuid: str) -> str:
    """
    Retrieve detailed information about a network edge by its endpoint node UUIDs.

    This tool fetches edge details by specifying the two nodes that the edge connects.
    Since edges in the network are bidirectional, the order of node1_uuid and node2_uuid
    does not matter - the API will find the edge connecting these two nodes regardless
    of which UUID is provided first. This is particularly useful when you know two nodes
    are connected (or want to verify connectivity) but don't have the edge UUID.

    Parameters
    ----------
    node1_uuid : str
        The unique identifier (UUID) of the first endpoint node.
        Must be a valid UUID of an existing node in the network.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    node2_uuid : str
        The unique identifier (UUID) of the second endpoint node.
        Must be a valid UUID of an existing node in the network.
        Must be different from node1_uuid.
        Example: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    Returns
    -------
    Dict[str, Any]
        A dictionary containing complete edge information:

        On Success:
        - uuid (str): Unique identifier for the edge
        - node1_uuid (str): UUID of the first endpoint node (as stored in database)
        - node2_uuid (str): UUID of the second endpoint node (as stored in database)
        - capacity_gbps (float): Total edge capacity in Gigabits per second
        - created_at (str): ISO 8601 timestamp when edge was created
        - updated_at (str): ISO 8601 timestamp of last modification

        On Failure:
        - error (str): Error message describing what went wrong
        - node1_uuid (str): Echo of the first requested node UUID
        - node2_uuid (str): Echo of the second requested node UUID

    Raises
    ------
    EdgeNotFoundError
        If no edge exists connecting the two specified nodes, or if the nodes
        are not directly connected in the network topology
    NodeNotFoundError
        If either node1_uuid or node2_uuid does not exist in the network
    ValidationError
        If node1_uuid and node2_uuid are the same (self-loops not allowed)
    APIConnectionError
        If unable to connect to the Network Simulator API
    APITimeoutError
        If the API request times out

    Examples
    --------
    Get edge between two known nodes:
        >>> get_edge_by_endpoints("550e8400-e29b-41d4-a716-446655440000",
        ...                        "6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        {"uuid": "7c9e6679...", "node1_uuid": "550e8400...", "capacity_gbps": 50.0, ...}

    Order doesn't matter (bidirectional):
        >>> # These two calls return the same edge:
        >>> get_edge_by_endpoints(node_a, node_b)
        >>> get_edge_by_endpoints(node_b, node_a)

    No direct connection exists:
        >>> get_edge_by_endpoints("boston-uuid", "miami-uuid")
        {"error": "Edge not found", "node1_uuid": "boston-uuid", "node2_uuid": "miami-uuid"}

    Notes
    -----
    - Edges are bidirectional and the query is order-agnostic; you can swap node1 and node2
    - This is useful for checking direct connectivity between two nodes
    - If no direct edge exists, nodes may still be reachable via a multi-hop path
    - Use find_and_plan_route() to compute multi-hop paths between nodes
    - The returned node1_uuid and node2_uuid may be in different order than your input
      (they reflect the order stored in the database)
    - Use get_edge_by_uuid() if you already have the edge UUID
    - Use get_node_by_uuid() to get details about the endpoint nodes
    - Approximately 200 bidirectional edges exist in the network
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        edge = client.get_edge_by_endpoints(node1_uuid, node2_uuid)

        return json.dumps(
            {
                "uuid": edge.uuid,
                "node1_uuid": edge.node1_uuid,
                "node2_uuid": edge.node2_uuid,
                "capacity_gbps": edge.capacity_gbps,
                "created_at": edge.created_at,
                "updated_at": edge.updated_at,
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "node1_uuid": node1_uuid,
                "node2_uuid": node2_uuid,
            }
        )
    finally:
        client.close()


@function_tool
async def get_node_by_uuid(node_uuid: str) -> str:
    """
    Retrieve detailed information about a specific network node by its UUID.

    This tool fetches complete details for a single node using its unique identifier.
    Use this when you have a node UUID from a previous query (like from a route or
    service) and need to get full information about that specific node, including
    its geographic location, vendor, and current capacity status.

    Parameters
    ----------
    node_uuid : str
        The unique identifier (UUID) of the node to retrieve.
        Must be a valid UUID of an existing node in the network.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    Returns
    -------
    Dict[str, Any]
        A dictionary containing complete node information:

        On Success:
        - uuid (str): Unique identifier for the node
        - name (str): Human-readable name (e.g., "Boston-MA", "New York-NY")
        - latitude (float): Latitude coordinate in degrees (-90 to 90)
        - longitude (float): Longitude coordinate in degrees (-180 to 180)
        - vendor (str): Network equipment vendor (e.g., "Cisco", "Juniper", "Agave Networks")
        - capacity_gbps (float): Total node capacity in Gigabits per second
        - free_capacity_gbps (float): Available (unused) capacity in Gbps
        - created_at (str): ISO 8601 timestamp when node was created
        - updated_at (str): ISO 8601 timestamp of last modification

        On Failure:
        - error (str): Error message describing what went wrong
        - node_uuid (str): Echo of the requested node UUID

    Raises
    ------
    NodeNotFoundError
        If the specified node UUID does not exist in the network
    APIConnectionError
        If unable to connect to the Network Simulator API
    APITimeoutError
        If the API request times out

    Examples
    --------
    Get details for a specific node:
        >>> get_node_by_uuid("550e8400-e29b-41d4-a716-446655440000")
        {"uuid": "550e8400...", "name": "Boston-MA", "capacity_gbps": 3501.0, ...}

    Node not found:
        >>> get_node_by_uuid("invalid-uuid")
        {"error": "Node not found", "node_uuid": "invalid-uuid"}

    Notes
    -----
    - This is useful when you have a node UUID from a route computation or service query
    - Free capacity is calculated as: total capacity - sum of all service demands at this node
    - The network contains approximately 48 nodes across the eastern United States
    - Use get_nodes_by_name() if you only know the node's name
    - Use get_nodes_by_location() if you want to find nodes near a geographic point
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        node = client.get_node(node_uuid)

        return json.dumps(
            {
                "uuid": node.uuid,
                "name": node.name,
                "latitude": node.latitude,
                "longitude": node.longitude,
                "vendor": node.vendor,
                "capacity_gbps": node.capacity_gbps,
                "free_capacity_gbps": node.free_capacity_gbps,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e), "node_uuid": node_uuid})
    finally:
        client.close()


@function_tool
async def find_and_plan_route(
    source_node_uuid: str, destination_node_uuid: str, demand_gbps: float = 5.0
) -> str:
    """
    Compute an optimal route between two nodes using A* pathfinding with capacity constraints.

    This tool uses the Network Simulator's A* pathfinding algorithm to find the shortest
    geographic path between two nodes that satisfies the specified bandwidth demand. The
    algorithm considers both distance (optimization goal) and available capacity (constraint)
    on each edge. It returns the complete path with detailed capacity and performance metrics.

    Parameters
    ----------
    source_node_uuid : str
        The unique identifier (UUID) of the source (starting) node.
        Must be a valid UUID of an existing node in the network.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    destination_node_uuid : str
        The unique identifier (UUID) of the destination (target) node.
        Must be a valid UUID of an existing node in the network.
        Must be different from source_node_uuid.
        Example: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    demand_gbps : float, optional
        The required bandwidth in Gigabits per second for this route.
        Default is 5.0 Gbps. Must be positive.
        The algorithm will only consider edges with sufficient available capacity.
        Example: 10.0 for a 10 Gbps connection

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the computed route and metadata:

        On Success:
        - success (bool): True if route was found
        - source_node_uuid (str): Echo of the source node UUID
        - destination_node_uuid (str): Echo of the destination node UUID
        - demand_gbps (float): Echo of the bandwidth demand
        - path_node_uuids (List[str]): Ordered list of node UUIDs forming the path
            First element is source, last element is destination
        - path_edge_uuids (List[str]): Ordered list of edge UUIDs forming the path
            Length is always len(path_node_uuids) - 1
        - total_distance_km (float): Total geographic distance of the path in kilometers
        - hop_count (int): Number of hops (edges) in the path
        - min_available_capacity_gbps (float): Bottleneck capacity along the route
            This is the lowest available capacity across all edges in the path
        - computation_time_ms (float): Time taken to compute the route in milliseconds
        - capacity_status (str): "SUFFICIENT" if route can handle the demand

        On Failure:
        - success (bool): False if no route was found
        - error (str): Description of the error
        - source_node_uuid (str): Echo of the source node UUID
        - destination_node_uuid (str): Echo of the destination node UUID
        - demand_gbps (float): Echo of the bandwidth demand

    Raises
    ------
    NodeNotFoundError
        If source or destination node UUID does not exist
    RouteNotFoundError
        If no feasible path exists that satisfies the capacity constraint
    ValidationError
        If source and destination are the same, or if demand_gbps is invalid
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Find a basic 5 Gbps route:
        >>> find_and_plan_route("source-uuid", "dest-uuid")
        {"success": True, "path_node_uuids": [...], "distance_km": 347.5, ...}

    Find a high-capacity 50 Gbps route:
        >>> find_and_plan_route("source-uuid", "dest-uuid", 50.0)
        {"success": True, "min_available_capacity_gbps": 55.0, ...}

    Route not found (insufficient capacity):
        >>> find_and_plan_route("source-uuid", "dest-uuid", 1000.0)
        {"success": False, "error": "No route found with sufficient capacity"}

    Notes
    -----
    - The A* algorithm uses geographic distance (haversine) as the heuristic
    - Optimization goal: minimize total path distance (km)
    - Constraint: every edge must have available_capacity >= demand_gbps
    - Available capacity = edge.capacity_gbps - sum(services using this edge)
    - The algorithm explores the network topology efficiently using a priority queue
    - Typical computation time is 1-10ms depending on network size and path length
    - The returned path is guaranteed to be valid and capacity-feasible
    - If multiple paths have the same distance, the algorithm returns one arbitrarily
    - This tool does NOT provision the service; it only computes the route
    - Use create_service() to actually provision a service along a computed route
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        route = client.compute_route(
            source_node_uuid=source_node_uuid,
            destination_node_uuid=destination_node_uuid,
            demand_gbps=demand_gbps,
        )

        # Check if route has sufficient capacity
        capacity_status = (
            "SUFFICIENT"
            if route.min_available_capacity >= demand_gbps
            else "INSUFFICIENT"
        )

        return json.dumps(
            {
                "success": True,
                "source_node_uuid": route.source_node_uuid,
                "destination_node_uuid": route.destination_node_uuid,
                "demand_gbps": route.demand_gbps,
                "path_node_uuids": route.path_node_uuids,
                "path_edge_uuids": route.path_edge_uuids,
                "total_distance_km": route.total_distance_km,
                "hop_count": route.hop_count,
                "min_available_capacity_gbps": route.min_available_capacity,
                "computation_time_ms": route.computation_time_ms,
                "capacity_status": capacity_status,
            }
        )

    except:
        return json.dumps(
            {
                "success": False,
                "error": f"No path exists with sufficient capacity for demand of {demand_gbps} Gbps",
                "source_node_uuid": source_node_uuid,
                "destination_node_uuid": destination_node_uuid,
                "demand_gbps": demand_gbps,
            }
        )
    finally:
        client.close()


# Create the testing agent
planning_agent = Agent(
    name="NetworkTestingAgent",
    instructions="""You are a simple testing agent for the Network Simulator API. YOU OPERATE STRICTLY USING PLAINTEXT. DO NOT USE MARKDOWN!

Your job is to help the user form a plan to create new services in their network.
Available tools:
- get_nodes_by_name: Search for nodes by name substring
- get_nodes_by_location: Find nodes within a geographic radius
- get_node_by_uuid: Get detailed information about a specific node by UUID
- get_edge_by_uuid: Get detailed information about a specific edge by UUID
- get_edge_by_endpoints: Get edge information by specifying the two endpoint node UUIDs
- get_node_services: Get services originating from a specific node
- find_and_plan_route: Compute an optimal route between two nodes
- create_service: Create a new network service by provisioning bandwidth along a path

Once the user finalizes their plan, provide a detailed provisioning guide with the following details:
1. The A-end node name and node UUID
2. The Z-end node name and node UUID
3. The service capacity
4. A list of intermediate node names and UUIDs
5. A list of intermediate edge names and UUIDs

Simply execute the requested tool calls and present the user with the results. NO IMAGES!""",
    model=OpenAIResponsesModel(model=GENERATIVE_MODEL, openai_client=llm_client),
    tools=[
        get_nodes_by_name,
        get_nodes_by_location,
        get_node_by_uuid,
        get_edge_by_uuid,
        get_edge_by_endpoints,
        get_node_services,
        find_and_plan_route,
    ],
    # model_settings=ModelSettings(reasoning=None),
)


def get_multiline_input() -> str:
    """Get multi-line input from user. Ends with triple quotes on a new line."""
    print(
        f'{Fore.YELLOW}[Multi-line mode: Type your message, end with """ on a new line]{Style.RESET_ALL}'
    )
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == '"""':
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)


def wrap_text(text: str, width: int = 70) -> str:
    """Wrap text to specified width while preserving paragraphs."""
    paragraphs = text.split("\n")
    wrapped_paragraphs = [
        textwrap.fill(p, width=width) if p.strip() else "" for p in paragraphs
    ]
    return "\n".join(wrapped_paragraphs)


async def main() -> None:
    """Run the planning agent in an interactive multi-turn chat loop."""
    # Initialize colorama for cross-platform color support
    colorama_init(autoreset=True)

    # Print header with colors
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{'Network Planning Agent':^70}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Ask questions about network nodes, routes, and services.")
    print(
        f"{Fore.YELLOW}Commands: 'exit', 'quit', 'help', or Ctrl+D to end | '\"\"\"' for multi-line input{Style.RESET_ALL}\n"
    )

    conversation_history = None
    turn_count = 0

    while True:
        try:
            # Display turn counter and prompt
            turn_count += 1
            print(f"{Fore.CYAN}[Turn {turn_count}]{Style.RESET_ALL}")
            user_input = input(f"{Fore.CYAN}You:{Style.RESET_ALL} ").strip()

            # Check for special commands
            if user_input.lower() in ["exit", "quit"]:
                print(f"\n{Fore.GREEN}Goodbye! Happy planning!{Style.RESET_ALL}")
                break

            # Help command
            if user_input.lower() in ["help", "?"]:
                print(f"\n{Fore.YELLOW}Available Commands:{Style.RESET_ALL}")
                print(
                    f"  {Fore.CYAN}exit, quit{Style.RESET_ALL} - End the conversation"
                )
                print(
                    f"  {Fore.CYAN}help, ?{Style.RESET_ALL}    - Show this help message"
                )
                print(
                    f'  {Fore.CYAN}"""{Style.RESET_ALL}        - Start multi-line input mode'
                )
                print(
                    f"  {Fore.CYAN}Ctrl+D{Style.RESET_ALL}     - End the conversation"
                )
                print(
                    f"  {Fore.CYAN}Ctrl+C{Style.RESET_ALL}     - Interrupt current operation\n"
                )
                turn_count -= 1  # Don't count help as a turn
                continue

            # Multi-line input mode
            if user_input == '"""':
                user_input = get_multiline_input()
                if not user_input.strip():
                    turn_count -= 1
                    continue

            # Skip empty inputs
            if not user_input:
                turn_count -= 1
                continue

            # Show processing indicator
            print(f"{Fore.YELLOW}[Processing...]{Style.RESET_ALL}", end="\r")

            # Run the agent with accumulated conversation history
            # First turn: pass string directly
            # Subsequent turns: append new user message to conversation history from to_input_list()
            if conversation_history is None:
                result = await Runner.run(planning_agent, user_input)
            else:
                # Append new user message to the history in proper format
                new_input = conversation_history + [
                    {"role": "user", "content": user_input}
                ]
                result = await Runner.run(planning_agent, new_input)

            # Clear processing indicator and print the agent's response
            print(" " * 20, end="\r")  # Clear the processing message
            print(f"\n{Fore.GREEN}Agent:{Style.RESET_ALL}")
            wrapped_output = wrap_text(result.final_output, width=68)
            print(f"{wrapped_output}\n")
            print(f"{Fore.CYAN}{'-' * 70}{Style.RESET_ALL}\n")

            # Update conversation history with full context for next turn using to_input_list()
            conversation_history = result.to_input_list()

        except EOFError:
            # Handle Ctrl+D
            print(f"\n\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print(f"\n\n{Fore.YELLOW}Interrupted. Goodbye!{Style.RESET_ALL}")
            break
        except Exception as e:
            # Handle other errors with better formatting
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}\n")
            turn_count -= 1  # Don't count error turns


if __name__ == "__main__":
    set_tracing_disabled(True)
    asyncio.run(main())
