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
    Create a parallel edge to add capacity to an existing connection.

    IMPORTANT CONSTRAINT: This tool can ONLY add capacity to existing edges.
    You cannot create entirely new connections between nodes that aren't already
    connected. This ensures network topology integrity.

    Use this tool when you need to increase bandwidth between two nodes that
    already have a connection but need more capacity for additional services.

    Args:
        node1_uuid: UUID of the first endpoint node
        node2_uuid: UUID of the second endpoint node
        capacity_gbps: Additional capacity to add in Gbps (must be > 0)

    Returns:
        JSON string containing:
        SUCCESS CASE:
        - uuid: New edge UUID
        - node1_uuid, node2_uuid: Endpoint UUIDs
        - capacity_gbps: Capacity of the new parallel edge
        - existing_edge_uuid: UUID of the original edge
        - created_at, updated_at: Timestamps
        - message: Success confirmation

        FAILURE CASE (no existing edge):
        - error: Explanation that no existing connection exists
        - constraint: Policy explanation
        - node1_uuid, node2_uuid, capacity_gbps: Request parameters

    Example:
        Nodes A and B have a 100 Gbps link that's heavily utilized.
        create_edge(uuid_A, uuid_B, 50.0) adds a parallel 50 Gbps link.
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    Delete a network edge (connection) from the network.

    IMPORTANT CONSTRAINT: You can only delete edges that are NOT being used
    by any active services. If services are using this edge, the deletion will
    fail with a conflict error.

    Use this tool to remove unused edges or clean up after deprovisioning services.

    Args:
        edge_uuid: UUID of the edge to delete

    Returns:
        JSON string containing:
        SUCCESS CASE:
        - message: Confirmation of deletion
        - edge_uuid: UUID of the deleted edge
        - deleted_at: Timestamp of deletion

        FAILURE CASE:
        - error: Explanation (e.g., edge in use by services, edge not found)
        - edge_uuid: UUID that was attempted

    Example:
        edge_uuid = "0c929850-79fc-4acd-a69d-163dc318353a"
        Deletes the edge if no services are using it
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    Provision a new network service along a specified path.

    This is the PRIMARY tool for service provisioning. It creates a service that
    reserves bandwidth on all edges in the path. The service will consume capacity
    from each edge it traverses.

    VALIDATION REQUIREMENTS:
    - Source must be the first node in path_node_uuids
    - Destination must be the last node in path_node_uuids
    - Number of edges must equal number of nodes minus 1
    - All edges must have sufficient available capacity for the demand
    - Path must be valid (consecutive nodes connected by edges)

    Args:
        name: Descriptive name for the service (e.g., "NYC-to-Boston-Service-001")
        source_node_uuid: UUID of the origin node
        destination_node_uuid: UUID of the destination node
        demand_gbps: Bandwidth to reserve in Gbps (must be > 0)
        path_node_uuids: Ordered list of node UUIDs from source to destination
        path_edge_uuids: Ordered list of edge UUIDs connecting the nodes

    Returns:
        JSON string containing:
        SUCCESS CASE:
        - uuid: Unique service identifier
        - name: Service name
        - source_node_uuid, destination_node_uuid: Endpoints
        - demand_gbps: Bandwidth reserved
        - hop_count: Number of hops (edges) in path
        - total_distance_km: Geographic distance of the path
        - path_node_uuids: Complete node path
        - path_edge_uuids: Complete edge path
        - service_timestamp: When service was created
        - created_at: Creation timestamp

        FAILURE CASE:
        - error: Explanation (capacity violation, invalid path, etc.)
        - Request parameters

    Example:
        name = "Service-NYC-BOS", source = uuid_NYC, destination = uuid_BOS,
        demand = 10.0, path_nodes = [uuid_NYC, uuid_ALB, uuid_BOS],
        path_edges = [edge_NYC_ALB, edge_ALB_BOS]
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    Delete an existing network service and free its reserved capacity.

    Use this tool to deprovision services that are no longer needed. Deleting
    a service will free up the bandwidth it was consuming on all edges in its path.

    Args:
        service_uuid: UUID of the service to delete

    Returns:
        JSON string containing:
        SUCCESS CASE:
        - message: Confirmation of deletion
        - service_uuid: UUID of the deleted service
        - deleted_at: Timestamp of deletion

        FAILURE CASE:
        - error: Explanation (service not found, etc.)
        - service_uuid: UUID that was attempted

    Example:
        service_uuid = "4b20d4ae-8932-4f05-b093-cc2202dd3e1e"
        Deletes the service and frees its reserved bandwidth
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: Annotate this
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    instructions="""
    You are a Network Provisioning Agent specialized in creating and managing network services and capacity.

    YOUR ROLE:
    - Provision new network services on planned paths
    - Add capacity to existing connections when needed
    - Delete services to free up bandwidth
    - Remove unused edges from the network
    - Ensure all operations maintain network integrity

    THE NETWORK:
    - 48 network nodes across the eastern United States
    - ~200 bidirectional edges (connections) with capacity limits
    - Services consume bandwidth on the edges they traverse
    - Network topology is protected - you can only expand existing connections

    YOUR TOOLS:
    1. create_service(...) - PRIMARY TOOL: Provision a new service on a path
    2. delete_service(service_uuid) - Remove a service and free its capacity
    3. create_edge(node1_uuid, node2_uuid, capacity_gbps) - Add capacity to existing connection
    4. delete_edge(edge_uuid) - Remove an unused edge

    CRITICAL CONSTRAINTS:
    1. SERVICES: Must have valid paths where:
       - Source is first node in path
       - Destination is last node in path
       - Edge count = node count - 1
       - All edges have sufficient capacity
    2. EDGES: Can ONLY create parallel edges on existing connections
       - Cannot create brand new connections between unconnected nodes
       - Can only delete edges not used by any service
    3. CAPACITY: All operations must respect capacity constraints

    WORKFLOW FOR SERVICE PROVISIONING:
    1. Receive a planned route from the planning agent with:
       - Source and destination UUIDs
       - Path nodes (ordered list)
       - Path edges (ordered list)
       - Required bandwidth (demand_gbps)
    2. Validate the path structure (counts match, endpoints correct)
    3. Call create_service() with all required parameters
    4. Confirm success or explain failure clearly

    OUTPUT FORMAT:
    When provisioning succeeds, include:
    - Service UUID (for future reference)
    - Service name
    - Endpoints (source and destination)
    - Bandwidth reserved (demand_gbps)
    - Number of hops
    - Total distance

    IMPORTANT NOTES:
    - Always validate path structure before calling create_service()
    - If capacity is insufficient, explain which edge is the bottleneck
    - When deleting, confirm the service/edge UUID exists
    - All tool responses are JSON strings - parse them to extract information
    - Be clear about success vs failure
    """,
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
