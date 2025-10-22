#!/usr/bin/env python3
"""
Provisioning Agent Starter - Exercise 7

TODO: Implement a provisioning agent that creates services on the network.

Your tasks:
1. Implement create_network_service() tool
2. Implement verify_service() tool
3. Write clear agent instructions
4. Test with planning agent output
"""
import os
from agents import Agent, Runner
from network_simulator_client import NetworkSimulatorClient, ServiceCreate
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==================== TOOLS ====================
# TODO: Implement these tool functions

def create_network_service(
    name: str,
    source_uuid: str,
    destination_uuid: str,
    demand_gbps: float,
    path_node_uuids: list,
    path_edge_uuids: list,
    total_distance_km: float
):
    """
    Provision a service on the network.
    
    Args:
        name: Service name
        source_uuid: Source node UUID
        destination_uuid: Destination node UUID
        demand_gbps: Bandwidth requirement
        path_node_uuids: Ordered list of nodes in path
        path_edge_uuids: Ordered list of edges in path
        total_distance_km: Total path distance
        
    Returns:
        Service creation result with UUID
        
    TODO:
    1. Create client
    2. Build ServiceCreate object
    3. Call client.create_service()
    4. Handle errors
    5. Format result
    6. Close client
    """
    # YOUR CODE HERE
    pass


def verify_service(service_uuid: str):
    """
    Verify a service exists and get its details.
    
    Args:
        service_uuid: UUID of service to verify
        
    Returns:
        Service details or error
        
    TODO:
    1. Create client  
    2. Call client.get_service()
    3. Handle ServiceNotFoundError
    4. Format result
    5. Close client
    """
    # YOUR CODE HERE
    pass


# ==================== AGENT ====================
# TODO: Create your provisioning agent

provisioning_agent = Agent(
    name="ProvisioningAgent",
    instructions="""
    TODO: Write instructions for your provisioning agent
    
    Hints:
    - Explain what the agent does
    - List available tools
    - Describe validation steps
    - Specify output format
    """,
    model="gpt-4o-mini",
    tools=[create_network_service, verify_service]
)


# ==================== TESTING ====================

def test_provisioning_agent():
    """Test your provisioning agent."""
    print("=" * 60)
    print(" Testing Provisioning Agent")
    print("=" * 60)
    
    # You'll need to get a route from planning agent first
    # Then provision a service using that route
    
    print("\nTODO: Implement tests")
    print("Hint: First get a route from planning agent, then provision it")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        exit(1)
        
    test_provisioning_agent()
