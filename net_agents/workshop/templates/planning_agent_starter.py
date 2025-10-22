#!/usr/bin/env python3
"""
Planning Agent Starter - Exercise 6

TODO: Implement a planning agent that finds viable paths in the network.

Your tasks:
1. Implement get_network_nodes() tool
2. Implement find_route() tool  
3. Write clear agent instructions
4. Test with various scenarios
"""
import os
from agents import Agent, Runner
from network_simulator_client import NetworkSimulatorClient
from dotenv import load_dotenv

load_dotenv()

# ==================== TOOLS ====================
# TODO: Implement these tool functions

def get_network_nodes():
    """
    Get all network nodes with their details.
    
    Returns a list of nodes with name, UUID, capacity, and location.
    
    TODO: 
    1. Create client
    2. Get all nodes
    3. Format for agent consumption
    4. Close client
    5. Return formatted list
    """
    # YOUR CODE HERE
    pass


def find_route(source_uuid: str, destination_uuid: str, demand_gbps: float = 5.0):
    """
    Find a route between two nodes with capacity check.
    
    Args:
        source_uuid: UUID of source node
        destination_uuid: UUID of destination node
        demand_gbps: Required bandwidth in Gbps
        
    Returns:
        Route information with path and capacity details
        
    TODO:
    1. Create client
    2. Call client.compute_route()
    3. Handle errors (RouteNotFoundError)
    4. Format result
    5. Close client
    6. Return result dict
    """
    # YOUR CODE HERE
    pass


# ==================== AGENT ====================
# TODO: Create your planning agent

planning_agent = Agent(
    name="PlanningAgent",
    instructions="""
    TODO: Write instructions for your planning agent
    
    Hints:
    - Explain what the agent does
    - List available tools
    - Describe the process to follow
    - Specify output format
    """,
    model="gpt-4o-mini",
    tools=[get_network_nodes, find_route]  # TODO: Make sure tools are implemented!
)


# ==================== TESTING ====================

def test_planning_agent():
    """Test your planning agent."""
    print("=" * 60)
    print(" Testing Planning Agent")
    print("=" * 60)
    
    # Test 1: Simple route by name
    print("\nTest 1: Route by name")
    result = Runner.run_sync(
        planning_agent,
        "Find a route from Albany-NY to Boston-MA with 5 Gbps demand"
    )
    print(result.final_output)
    
    # Test 2: TODO: Add more tests
    # - Route with UUID
    # - High demand (may fail)
    # - Try different node pairs
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        exit(1)
        
    test_planning_agent()
