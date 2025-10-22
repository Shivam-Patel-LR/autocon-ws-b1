#!/usr/bin/env python3
"""Quick test of the support agent."""
import os
from agents import Runner
from net_agents.workshop.ex1_support_agent import support_agent
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("Error: Need OPENAI_API_KEY")
    exit(1)

# Test the support agent
print("Testing support agent...\n")

result = Runner.run_sync(
    support_agent, "What is the network simulator and how many nodes does it have?"
)

print("Agent Response:")
print(result.final_output)
print("\n✓ Support agent test successful!")
