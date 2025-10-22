#!/usr/bin/env python3
"""
Setup Verification Script

Checks that all workshop requirements are properly installed and configured.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def check_api_connection():
    """Verify network simulator API is running."""
    try:
        from network_simulator_client import NetworkSimulatorClient

        client = NetworkSimulatorClient(base_url="http://localhost:8003", timeout=5.0)
        health = client.health_check()
        print(f"✓ Network Simulator API: {health.status}")

        stats = client.get_database_stats()
        print(
            f"✓ Network loaded: {stats.nodes} nodes, {stats.edges} edges, {stats.services} services"
        )

        client.close()
        return True
    except Exception as e:
        print(f"✗ API Connection Failed: {e}")
        print("  Make sure the simulator is running:")
        print("    cd network_simulator")
        print("    docker compose up -d")
        return False


def check_openai_agents():
    """Verify OpenAI Agents SDK is installed."""
    try:
        import agents

        print(f"✓ OpenAI Agents SDK installed (version {agents.__version__})")
        return True
    except ImportError:
        print("✗ OpenAI Agents SDK not installed")
        print("  Install with: uv pip install openai-agents")
        return False


def check_api_key():
    """Verify OpenAI API key is configured."""
    # Try loading from .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    status = True

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        print("✗ AZURE_OPENAI_API_KEY not set")
        print("\t-> Check that your API key is correctly formatted")
        status = False
    else:
        masked_key = api_key[:7] + "..." + api_key[-4:]
        print(f"✓ Azure OpenAI API key configured ({masked_key})")

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("✗ AZURE_OPENAI_ENDPOINT not set")
        print("\t-> Check that your API endpoint is correctly formatted")
        status = False
    else:
        print(f"✓ Azure OpenAI endpoint configured ({endpoint})")

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        print("✗ AZURE_OPENAI_DEPLOYMENT not set")
        print("\t-> Check that your model deployment is correctly formatted")
        status = False
    else:
        print(f"✓ Azure OpenAI deployment configured ({deployment})")

    client = OpenAI(
        api_key=api_key,
        base_url=endpoint,
    )

    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a simple arithmetic problem solver. You answer only with the numeric answer.",
                },
                {
                    "role": "user",
                    "content": "What is 2+2?",
                },
            ],
        )
        ans = int(completion.choices[0].message.content)

        if ans != 4:
            print("LLM Completion not correct!")
            status = False
        else:
            print("LLM generation successful!")

    except:
        print("Failed to test LLM completion!")

    return status


def check_python_version():
    """Verify Python version is sufficient."""
    version = sys.version_info
    if version >= (3, 12):
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (requires 3.12+)")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print(" Workshop Setup Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("OpenAI Agents SDK", check_openai_agents),
        ("OpenAI API Key", check_api_key),
        ("Network Simulator API", check_api_connection),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {name}: Unexpected error - {e}")
            results.append(False)
        print()

    print("=" * 60)
    if all(results):
        print("Setup complete! You're ready to start building agents.")
        print()
        print("Next steps:")
        print("  1. Read NETWORK_REFERENCE.md to understand the network")
        print("  2. Start EXERCISE_GUIDE.md with Exercise 1")
        print("  3. Build your first agent!")
        return 0
    else:
        print("Setup incomplete. Please fix the issues above.")
        print()
        print("See SETUP.md for detailed installation instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
