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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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
    TODO: What this  tool does, when to call it, and how it should be used
    """
    client = NetworkSimulatorClient(base_url="http://network-simulator:8003")

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

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"No path exists with sufficient capacity for demand of {demand_gbps} Gbps. Details: {str(e)}",
                "source_node_uuid": source_node_uuid,
                "destination_node_uuid": destination_node_uuid,
                "demand_gbps": demand_gbps,
            }
        )
    finally:
        client.close()


# Create the testing agent
planning_agent = Agent(
    name="NetworkPlanningAgent",
    instructions="""
    TODO: Write a system prompt
    """,
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
