#!/usr/bin/env python3
"""
Workshop Support Agent - Exercise 4 Solution

A support agent that helps workshop participants understand the network simulator
and OpenAI Agents SDK without using any tools.
"""
import asyncio
import textwrap
from datetime import datetime
from colorama import Fore, Style, init as colorama_init
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled, Runner
from dotenv import load_dotenv
from config import llm_client, GENERATIVE_MODEL

# Load environment variables
load_dotenv()

with open("./docs/SETUP.md", "r", encoding="utf-8") as f:
    setup_docs = f.read()

with open("./docs/README.md", "r", encoding="utf-8") as f:
    readme_docs = f.read()

with open("./docs/NETWORK_REFERENCE.md", "r", encoding="utf-8") as f:
    net_ref_docs = f.read()

with open("./docs/EXERCISE_GUIDE.md", "r", encoding="utf-8") as f:
    ex_guide_docs = f.read()

WORKSHOP_DOCS = f"""
NETWORK SIMULATOR OVERVIEW:
- 48 nodes distributed across eastern US
- ~200 bidirectional edges (connections)
- ~100 services already provisioned
- Geographic routing with real distances
- Capacity constraints on nodes and edges

KEY SDK METHODS:
- client.get_nodes() - Retrieve all network nodes
- client.get_node(uuid) - Get specific node details
- client.search_nodes_by_name(substring) - Find nodes by name
- client.compute_route(source, dest, demand_gbps) - A* pathfinding
- client.create_service(service_data) - Provision a service
- client.get_capacity_summary() - Check network utilization
- client.get_capacity_violations() - Find oversubscribed edges

OPENAI AGENTS SDK:
- Import: from agents import Agent, Runner
- Create agent: Agent(name="Name", instructions="...")
- Run agent: Runner.run_sync(agent, "prompt") or await Runner.run(agent, "prompt")
- Agents have: name, instructions, tools (optional), handoffs (optional)
- Results have: final_output property with agent response

WORKSHOP EXERCISES:
1. Generative AI Frameworks - Compare LangChain vs OpenAI Agents SDK
2. Agentic Design Patterns - Centralized vs decentralized
3. Segmentation - Divide responsibilities effectively
4. Support Agent - Build agent without tools (this one!)
5. Network Problem - Understand the topology
6. Planning Agent - Find routes with capacity checking
7. Provisioning Agent - Create services on network
8. Iterative Improvement - Refine prompts and flows
9. Full Workflow - Integrate all agents

Supporting Documentation:

# Setup Information
{setup_docs}

# README.md 
{readme_docs}

# Network Reference
{net_ref_docs}

# Exercise Guide
{ex_guide_docs}
"""

# Create the support agent
support_agent = Agent(
    name="SupportAgent",
    instructions=f"""
You are a helpful workshop assistant for "Building AI Agents for Smarter Networks".

Your role:
- Help participants understand the network simulator and SDK
- Provide hints and guidance for exercises without giving complete solutions
- Explain OpenAI Agents SDK concepts clearly
- Stay encouraging and patient

Here is the workshop documentation:
{WORKSHOP_DOCS}

Key points:
- Give hints, not complete code solutions
- If asked about tools, explain you don't have access to execute anything
- For SDK questions, show small example snippets
- For exercise help, guide without solving completely
- Be concise but thorough

What you DON'T do:
- Execute code or call APIs  
- Access the actual network
- Provide complete exercise solutions (hints only!)
- Make up information not in the documentation

If you don't know something, say so and suggest where to look (SETUP.md, NETWORK_REFERENCE.md, EXERCISE_GUIDE.md).
""",
    model=OpenAIChatCompletionsModel(model=GENERATIVE_MODEL, openai_client=llm_client),
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
    """Run the support agent in an interactive multi-turn chat loop."""
    # Initialize colorama for cross-platform color support
    colorama_init(autoreset=True)

    # Print header with colors
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{'Workshop Support Agent':^70}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(
        f"{Fore.YELLOW}Ask questions about the workshop, network simulator, or OpenAI Agents SDK."
    )
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
                print(f"\n{Fore.GREEN}Goodbye! Happy coding!{Style.RESET_ALL}")
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
            # Subsequent turns: combine to_input_list() with new user message
            if conversation_history is None:
                result = await Runner.run(support_agent, user_input)
            else:
                # Append new user message to history in proper format
                new_input = conversation_history + [
                    {"role": "user", "content": user_input}
                ]
                result = await Runner.run(support_agent, new_input)

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
