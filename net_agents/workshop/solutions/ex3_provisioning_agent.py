#!/usr/bin/env python3
"""
Network Provisioning Agent - Exercise 3

A provisioning agent that creates and manages network edges and services.
This agent works in tandem with the planning agent to execute provisioning
plans by creating edges and services in the Network Simulator.
"""
import asyncio
import json
import textwrap
from datetime import datetime, timezone
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
from network_simulator_client.models import EdgeCreate, ServiceCreate

# Load environment variables
load_dotenv()


@function_tool
async def create_edge(node1_uuid: str, node2_uuid: str, capacity_gbps: float) -> str:
    """
    Attempt to create an edge between two network nodes (with constraint).

    IMPORTANT CONSTRAINT: This tool enforces a business rule that edges can only be
    created where a connection already exists between two nodes. This represents the
    concept of expanding capacity on existing network links rather than creating
    entirely new physical connections. You cannot create edges between nodes that
    are not already connected.

    NOTE: The underlying database also enforces uniqueness, so even if an edge exists,
    you cannot create a duplicate edge between the same two nodes. This constraint
    checks first whether ANY connection exists before attempting creation.

    Parameters
    ----------
    node1_uuid : str
        The unique identifier (UUID) of the first endpoint node.
        Must be a valid UUID of an existing node in the network.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    node2_uuid : str
        The unique identifier (UUID) of the second endpoint node.
        Must be a valid UUID of an existing node in the network.
        Must be different from node1_uuid (self-loops not allowed).
        An edge must already exist between these two nodes.
        Example: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    capacity_gbps : float
        The capacity for the edge in Gigabits per second.
        Must be a positive value greater than 0.
        Example: 50.0 for a 50 Gbps edge

    Returns
    -------
    str
        JSON string containing the result:

        On Success (edge exists, creation allowed by constraint but may fail on duplicate):
        - uuid (str): Unique identifier for the created edge (if successful)
        - node1_uuid (str): UUID of the first endpoint node
        - node2_uuid (str): UUID of the second endpoint node
        - capacity_gbps (float): Capacity of the edge in Gbps
        - existing_edge_uuid (str): UUID of the pre-existing edge
        - created_at (str): ISO 8601 timestamp when edge was created
        - updated_at (str): ISO 8601 timestamp of last update
        - message (str): Success confirmation message

        On Constraint Failure (no edge exists):
        - error (str): "Cannot create edge: no existing connection between these nodes"
        - node1_uuid (str): Echo of the first node UUID
        - node2_uuid (str): Echo of the second node UUID
        - capacity_gbps (float): Echo of the requested capacity
        - constraint (str): Explanation of constraint

        On API Failure (duplicate edge or other error):
        - error (str): Error message from API
        - node1_uuid (str): Echo of the first node UUID
        - node2_uuid (str): Echo of the second node UUID
        - capacity_gbps (float): Echo of the requested capacity

    Raises
    ------
    NodeNotFoundError
        If either node1_uuid or node2_uuid does not exist in the network
    ValidationError
        If capacity_gbps is invalid (not positive) or if node1_uuid equals node2_uuid,
        or if no existing edge exists between the nodes (constraint violation),
        or if edge already exists between these nodes (database uniqueness constraint)
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Constraint failure - no existing connection:
        >>> create_edge(boston_uuid, miami_uuid, 100.0)
        {"error": "Cannot create edge: no existing connection between these nodes", ...}

    Constraint passed but duplicate edge:
        >>> # Edge already exists between node1 and node2
        >>> create_edge(node1_uuid, node2_uuid, 50.0)
        {"error": "[HTTP 400] Edge between these nodes already exists", ...}

    Notes
    -----
    - CONSTRAINT: An edge must already exist between the two nodes to pass validation
    - This business rule represents capacity expansion intent, not new physical links
    - The database enforces uniqueness, preventing duplicate edges between same nodes
    - This constraint adds a pre-check before attempting API edge creation
    - Edges are bidirectional; order of node1 and node2 doesn't affect functionality
    - Use delete_edge() to remove edges when no longer needed
    - Edges cannot be deleted if they are being used by active services
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        # First, check if an edge already exists between these nodes
        # This enforces the constraint that we can only expand existing capacity
        existing_edge = None
        try:
            existing_edge = client.get_edge_by_endpoints(node1_uuid, node2_uuid)
        except Exception:
            # No existing edge found - cannot proceed
            return json.dumps(
                {
                    "error": "Cannot create edge: no existing connection between these nodes. "
                    "Edges can only be created to expand capacity on existing links.",
                    "node1_uuid": node1_uuid,
                    "node2_uuid": node2_uuid,
                    "capacity_gbps": capacity_gbps,
                    "constraint": "An existing edge must be present to add parallel capacity",
                }
            )

        # If we get here, an edge exists - proceed with creating parallel edge
        edge_create = EdgeCreate(
            node1_uuid=node1_uuid,
            node2_uuid=node2_uuid,
            capacity_gbps=capacity_gbps,
        )

        edge = client.create_edge(edge_create)

        return json.dumps(
            {
                "uuid": edge.uuid,
                "node1_uuid": edge.node1_uuid,
                "node2_uuid": edge.node2_uuid,
                "capacity_gbps": edge.capacity_gbps,
                "existing_edge_uuid": existing_edge.uuid,
                "created_at": edge.created_at,
                "updated_at": edge.updated_at,
                "message": f"Parallel edge created successfully, adding {capacity_gbps} Gbps capacity to existing connection between nodes",
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "node1_uuid": node1_uuid,
                "node2_uuid": node2_uuid,
                "capacity_gbps": capacity_gbps,
            }
        )
    finally:
        client.close()


@function_tool
async def delete_edge(edge_uuid: str) -> str:
    """
    Delete an existing network edge by its UUID.

    This tool removes an edge from the network topology. The edge can only be
    deleted if it is not currently being used by any active services. If services
    are using this edge, they must be deleted first before the edge can be removed.

    Parameters
    ----------
    edge_uuid : str
        The unique identifier (UUID) of the edge to delete.
        Must be a valid UUID of an existing edge in the network.
        Example: "7c9e6679-7425-40de-944b-e07fc1f90ae7"

    Returns
    -------
    str
        JSON string containing the deletion result:

        On Success:
        - message (str): Success confirmation message
        - edge_uuid (str): UUID of the deleted edge
        - deleted_at (str): ISO 8601 timestamp of deletion

        On Failure:
        - error (str): Error message describing what went wrong
        - edge_uuid (str): Echo of the requested edge UUID

    Raises
    ------
    EdgeNotFoundError
        If the specified edge UUID does not exist in the network
    ResourceConflictError
        If the edge is currently being used by one or more services
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Delete an unused edge:
        >>> delete_edge("7c9e6679-7425-40de-944b-e07fc1f90ae7")
        {"message": "Edge deleted successfully", "edge_uuid": "7c9e6679..."}

    Edge in use by services:
        >>> delete_edge("7c9e6679-7425-40de-944b-e07fc1f90ae7")
        {"error": "Cannot delete edge: currently used by 3 services", ...}

    Edge not found:
        >>> delete_edge("invalid-uuid")
        {"error": "Edge not found", "edge_uuid": "invalid-uuid"}

    Notes
    -----
    - Deletion is permanent and cannot be undone
    - All services using this edge must be deleted first
    - Use get_services_by_edge() to check which services are using the edge
    - After deletion, any routes using this edge will need to be recalculated
    - Consider the impact on network connectivity before deleting edges
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        client.delete_edge(edge_uuid)

        return json.dumps(
            {
                "message": f"Edge {edge_uuid} deleted successfully",
                "edge_uuid": edge_uuid,
                "deleted_at": datetime.now(timezone.utc).isoformat() + "Z",
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e), "edge_uuid": edge_uuid})
    finally:
        client.close()


@function_tool
async def create_service(
    name: str,
    source_node_uuid: str,
    destination_node_uuid: str,
    demand_gbps: float,
    path_node_uuids: list[str],
    path_edge_uuids: list[str],
) -> str:
    """
    Create a new service along a specified network path.

    This tool provisions a service (network connection) with allocated bandwidth
    along a pre-computed path through the network. The service reserves the specified
    bandwidth (demand_gbps) on all edges in the path. The path must be valid, with
    all nodes and edges existing and sufficient capacity available.

    Parameters
    ----------
    name : str
        Human-readable name for the service.
        Should be descriptive and unique.
        Example: "Service-NYC-BOS-001" or "CustomerA-Primary-Link"

    source_node_uuid : str
        The unique identifier (UUID) of the source (origin) node.
        Must be a valid UUID of an existing node in the network.
        Must match the first node in path_node_uuids.
        Example: "550e8400-e29b-41d4-a716-446655440000"

    destination_node_uuid : str
        The unique identifier (UUID) of the destination (target) node.
        Must be a valid UUID of an existing node in the network.
        Must match the last node in path_node_uuids.
        Must be different from source_node_uuid.
        Example: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    demand_gbps : float
        The required bandwidth for this service in Gigabits per second.
        Must be positive and greater than 0.
        This bandwidth will be reserved on all edges in the path.
        Example: 10.0 for a 10 Gbps service

    path_node_uuids : list[str]
        Ordered list of node UUIDs forming the service path.
        Must start with source_node_uuid and end with destination_node_uuid.
        Must contain at least 2 nodes (source and destination).
        Each consecutive pair of nodes must be connected by an edge.
        Example: ["node1-uuid", "node2-uuid", "node3-uuid"]

    path_edge_uuids : list[str]
        Ordered list of edge UUIDs forming the service path.
        Must contain exactly len(path_node_uuids) - 1 edges.
        Each edge must connect the corresponding consecutive nodes.
        All edges must have sufficient available capacity for demand_gbps.
        Example: ["edge1-uuid", "edge2-uuid"]

    total_distance_km : float
        Total geographic distance of the path in kilometers.
        Must be non-negative.
        Should match the sum of distances between consecutive nodes.
        Example: 347.5

    routing_stage : str, optional
        Routing stage identifier for tracking different routing phases.
        Must be either "stage_a" or "stage_b".
        Default: "stage_a"
        Example: "stage_b" for secondary routing phase

    Returns
    -------
    str
        JSON string containing the created service information:

        On Success:
        - uuid (str): Unique identifier for the newly created service
        - name (str): Service name
        - source_node_uuid (str): UUID of the source node
        - destination_node_uuid (str): UUID of the destination node
        - demand_gbps (float): Bandwidth demand in Gbps
        - hop_count (int): Number of hops (edges) in the path
        - total_distance_km (float): Total path distance in km
        - routing_stage (str): Routing stage identifier
        - path_node_uuids (List[str]): Node UUIDs in the path
        - path_edge_uuids (List[str]): Edge UUIDs in the path
        - service_timestamp (str): ISO 8601 timestamp when service was created
        - created_at (str): ISO 8601 timestamp of database creation
        - message (str): Success confirmation message

        On Failure:
        - error (str): Error message describing what went wrong
        - name (str): Echo of the requested service name
        - source_node_uuid (str): Echo of the source node UUID
        - destination_node_uuid (str): Echo of the destination node UUID

    Raises
    ------
    NodeNotFoundError
        If source, destination, or any path node does not exist
    EdgeNotFoundError
        If any path edge does not exist
    ValidationError
        If path is invalid, capacity insufficient, or parameters are inconsistent
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Create a service using a computed route:
        >>> create_service(
        ...     name="Service-NYC-BOS-001",
        ...     source_node_uuid="node1-uuid",
        ...     destination_node_uuid="node3-uuid",
        ...     demand_gbps=10.0,
        ...     path_node_uuids=["node1-uuid", "node2-uuid", "node3-uuid"],
        ...     path_edge_uuids=["edge1-uuid", "edge2-uuid"]
        ... )
        {"uuid": "service-123", "hop_count": 2, "message": "Service created successfully"}

    Invalid path (edge count mismatch):
        >>> create_service(..., path_node_uuids=[3 nodes], path_edge_uuids=[1 edge], ...)
        {"error": "Edge count must equal node count - 1", ...}

    Insufficient capacity:
        >>> create_service(..., demand_gbps=1000.0, ...)
        {"error": "Insufficient capacity on edge edge1-uuid", ...}

    Notes
    -----
    - Service creation reserves bandwidth on all edges in the path
    - Path validation ensures all nodes and edges exist and are properly connected
    - Each edge's available capacity is reduced by demand_gbps after service creation
    - Use the find_and_plan_route() tool from the planning agent to compute valid paths
    - Services can be deleted using delete_service() to free up capacity
    - Service timestamps track when the service was logically created vs. database creation
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        service_create = ServiceCreate(
            name=name,
            source_node_uuid=source_node_uuid,
            destination_node_uuid=destination_node_uuid,
            demand_gbps=demand_gbps,
            path_node_uuids=path_node_uuids,
            path_edge_uuids=path_edge_uuids,
            service_timestamp=datetime.now(timezone.utc).isoformat() + "Z",
        )

        service = client.create_service(service_create)

        return json.dumps(
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
                "created_at": service.created_at,
                "message": f"Service '{name}' created successfully with {service.hop_count} hops",
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "name": name,
                "source_node_uuid": source_node_uuid,
                "destination_node_uuid": destination_node_uuid,
            }
        )
    finally:
        client.close()


@function_tool
async def delete_service(service_uuid: str) -> str:
    """
    Delete an existing service and free up its reserved bandwidth.

    This tool removes a service from the network and releases the bandwidth
    (demand_gbps) that was reserved on all edges in the service's path. After
    deletion, the freed capacity becomes available for other services.

    Parameters
    ----------
    service_uuid : str
        The unique identifier (UUID) of the service to delete.
        Must be a valid UUID of an existing service in the network.
        Example: "service-uuid-123"

    Returns
    -------
    str
        JSON string containing the deletion result:

        On Success:
        - message (str): Success confirmation message
        - service_uuid (str): UUID of the deleted service
        - deleted_at (str): ISO 8601 timestamp of deletion

        On Failure:
        - error (str): Error message describing what went wrong
        - service_uuid (str): Echo of the requested service UUID

    Raises
    ------
    ServiceNotFoundError
        If the specified service UUID does not exist in the network
    APIConnectionError
        If unable to connect to the Network Simulator API

    Examples
    --------
    Delete a service:
        >>> delete_service("service-uuid-123")
        {"message": "Service service-uuid-123 deleted successfully", ...}

    Service not found:
        >>> delete_service("invalid-uuid")
        {"error": "Service not found", "service_uuid": "invalid-uuid"}

    Notes
    -----
    - Deletion is permanent and cannot be undone
    - Bandwidth reserved by the service is immediately freed on all path edges
    - After deletion, edge utilization metrics are automatically updated
    - Use get_service() before deletion if you need to save service details
    - Deleting a service does not delete the nodes or edges it used
    - Consider checking capacity utilization before and after deletion
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        client.delete_service(service_uuid)

        return json.dumps(
            {
                "message": f"Service {service_uuid} deleted successfully",
                "service_uuid": service_uuid,
                "deleted_at": datetime.now(timezone.utc).isoformat() + "Z",
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e), "service_uuid": service_uuid})
    finally:
        client.close()


@function_tool
async def get_database_stats() -> str:
    """
    Retrieve current database statistics including counts of all network entities.

    This tool provides a high-level overview of the network topology by returning
    the total counts of nodes, edges, and services currently in the database. It's
    useful for monitoring the network state and verifying provisioning operations.

    Returns
    -------
    str
        JSON string containing database statistics:

        - nodes (int): Total number of network nodes in the database
        - edges (int): Total number of edges (connections) in the database
        - services (int): Total number of provisioned services in the database
        - timestamp (str): ISO 8601 timestamp when statistics were retrieved

    Raises
    ------
    APIConnectionError
        If unable to connect to the Network Simulator API
    APITimeoutError
        If the API request times out

    Examples
    --------
    Get current network statistics:
        >>> get_database_stats()
        {"nodes": 48, "edges": 196, "services": 150, "timestamp": "2024-01-15T12:00:00Z"}

    After creating new edges:
        >>> # Initial: {"nodes": 48, "edges": 196, "services": 150}
        >>> create_edge(node1, node2, 50.0)
        >>> get_database_stats()
        {"nodes": 48, "edges": 197, "services": 150, ...}  # Edge count increased

    Notes
    -----
    - Statistics reflect the current state of the database
    - Useful for verifying successful creation or deletion operations
    - Counts include all entities, both active and recently modified
    - The typical network has ~48 nodes, ~200 edges, and ~100+ services
    - Use this tool to monitor network growth over time
    - Statistics query is fast and does not impact network performance
    """
    client = NetworkSimulatorClient(base_url="http://localhost:8003")

    try:
        stats = client.get_database_stats()

        return json.dumps(
            {
                "nodes": stats.nodes,
                "edges": stats.edges,
                "services": stats.services,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        client.close()


# Create the provisioning agent
provisioning_agent = Agent(
    name="NetworkProvisioningAgent",
    instructions="""You are a network provisioning agent for the Network Simulator API. YOU OPERATE STRICTLY USING PLAINTEXT. DO NOT USE MARKDOWN!

Your job is to execute provisioning operations based on user requests by calling the appropriate tools.

Available tools:
- create_edge: Add parallel capacity to an existing edge (CONSTRAINT: can only create edges where a connection already exists between nodes - this represents capacity expansion, not new physical links)
- delete_edge: Delete an existing edge by UUID (only if not used by services)
- create_service: Provision a new service along a specified path with bandwidth reservation
- delete_service: Delete an existing service by UUID and free up its bandwidth
- get_database_stats: Get current counts of nodes, edges, and services

IMPORTANT: When creating edges, you can ONLY add capacity to existing connections. You cannot create edges between nodes that are not already connected. This represents expanding capacity on existing links rather than building new physical infrastructure.

When creating services, ensure you have:
1. A valid path (from the planning agent's find_and_plan_route tool)
2. Source and destination node UUIDs
3. Path node UUIDs (ordered list)
4. Path edge UUIDs (ordered list, length = node count - 1)
5. Total distance in km
6. Bandwidth demand in Gbps

Execute the requested operations and present clear results to the user. NO IMAGES!""",
    model=OpenAIResponsesModel(model=GENERATIVE_MODEL, openai_client=llm_client),
    tools=[
        create_edge,
        delete_edge,
        create_service,
        delete_service,
        get_database_stats,
    ],
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
    """Run the provisioning agent in an interactive multi-turn chat loop."""
    # Initialize colorama for cross-platform color support
    colorama_init(autoreset=True)

    # Print header with colors
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{'Network Provisioning Agent':^70}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Provision edges and services in the network.")
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
                print(f"\n{Fore.GREEN}Goodbye! Happy provisioning!{Style.RESET_ALL}")
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
            if conversation_history is None:
                result = await Runner.run(provisioning_agent, user_input)
            else:
                new_input = conversation_history + [
                    {"role": "user", "content": user_input}
                ]
                result = await Runner.run(provisioning_agent, new_input)

            # Clear processing indicator and print the agent's response
            print(" " * 20, end="\r")  # Clear the processing message
            print(f"\n{Fore.GREEN}Agent:{Style.RESET_ALL}")
            wrapped_output = wrap_text(result.final_output, width=68)
            print(f"{wrapped_output}\n")
            print(f"{Fore.CYAN}{'-' * 70}{Style.RESET_ALL}\n")

            # Update conversation history with full context for next turn
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
