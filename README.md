# Network Agents Workshop

This repository contains hands-on exercises for building AI agents that interact with network infrastructure through a simulated network environment. Participants will learn to create agents for network support, planning, and provisioning tasks.

## Workshop Overview

The workshop covers practical exercises involving:
- Network topology analysis
- Route planning and optimization
- Capacity management
- Service provisioning
- AI agent development patterns

## Setup (Docker Compose - Recommended)

The easiest way to get started is using Docker Compose which handles all dependencies automatically:

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (Docker Desktop not required on Linux)
- [Git](https://git-scm.com/)

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd autocon-ws-b1

# Start everything with one command
docker-compose up -d

# Enter the workshop environment
docker-compose exec workshop bash

# Verify setup is working
verify-setup
```

That's it! The setup includes:
- ✅ Network simulator API running on http://localhost:8003  
- ✅ Workshop development environment with all dependencies
- ✅ Pre-built images (no local building required)
- ✅ Persistent data volumes
- ✅ Jupyter notebook available on http://localhost:8888

## Alternative Setup Options

### Option 1: VSCode DevContainer

The easiest way to get started is using the provided VSCode devcontainer that handles all dependencies automatically:

1. **Prerequisites:**
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in DevContainer:**
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd autocon-ws-b1
   
   # Open in VSCode
   code .
   ```
   
3. **Start DevContainer:**
   - VSCode should prompt you to "Reopen in Container"
   - Or use Command Palette (Ctrl+Shift+P / Cmd+Shift+P) � "Dev Containers: Reopen in Container"
   - Wait for the container to build (first time only)

4. **Verify Setup:**
   ```bash
   # In the VSCode terminal inside the container
   cd net_agents
   python ex0_verify_setup.py
   ```

### Option 2: Manual Docker Setup

Pre-built Docker images are available from GitHub Container Registry:

#### Authentication
```bash
# Authenticate with GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

#### Network Simulator
```bash
# Pull and run the network simulator
docker pull ghcr.io/OWNER/network-simulator:latest

# Run with persistent data
mkdir -p ./data ./output
docker run -d \
  --name network-simulator \
  -p 8003:8003 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  ghcr.io/OWNER/network-simulator:latest

# Verify it's running
curl http://localhost:8003/health
```

### Option 3: Local Installation (Not Recommended)

If you prefer to install dependencies locally:

#### Prerequisites

**Python 3.8+ Installation:**
- **macOS**: `brew install python` or download from [python.org](https://python.org)
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo yum install python3 python3-pip` (RHEL/CentOS)
- **Windows**: Download from [python.org](https://python.org) or `winget install Python.Python.3`

#### Setup Steps

1. **Create Python Environment:**
   ```bash
   # Verify Python version
   python --version  # or python3 --version on some systems
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # macOS/Linux:
   source venv/bin/activate
   
   # Windows (Command Prompt):
   venv\Scripts\activate.bat
   
   # Windows (PowerShell):
   venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies:**
   ```bash
   # Install main requirements
   pip install -r requirements.txt
   
   # Install the network client SDK
   cd net_agents
   pip install -e .
   cd ..
   ```

3. **Start Network Simulator:**
   ```bash
   cd network_simulator
   
   # macOS/Linux:
   python -m uvicorn api.api:app --host 0.0.0.0 --port 8003 --app-dir src
   
   # Windows:
   python -m uvicorn api.api:app --host 0.0.0.0 --port 8003 --app-dir src
   ```

## Workshop Structure

### Exercises Directory: `net_agents/workshop/`

1. **ex0_verify_setup.py** - Verify your environment is working
2. **ex1_support_agent.py** - Build a network support agent
3. **ex2_planning_agent.py** - Create a network planning agent  
4. **ex3_provisioning_agent.py** - Develop a service provisioning agent

### Solutions Directory: `net_agents/workshop/solutions/`
Reference implementations are provided for each exercise.

### Network Simulator Client: `net_agents/network_simulator_client/`
SDK for interacting with the network simulator API. See `net_agents/README.md` for detailed documentation.

## Getting Started

### Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Enter workshop environment
docker-compose exec workshop bash

# View logs
docker-compose logs -f

# Stop all services  
docker-compose down

# Restart services
docker-compose restart

# Pull latest images
docker-compose pull
```

### Workshop Commands (inside container)

```bash
# Verify everything works
verify-setup

# Run tests
run-tests  

# Start Jupyter notebook (http://localhost:8888)
start-jupyter

# Run exercises manually
cd net_agents/workshop
python ex0_verify_setup.py
python ex1_support_agent.py
```

## Environment Variables

The network simulator supports several configuration options:

| Variable | Default | Description |
|----------|---------|-------------|
| `FORCE_REBUILD` | `false` | Force rebuild of network data |
| `SKIP_VERIFICATION` | `false` | Skip database verification |
| `GENERATE_SERVICES` | `true` | Generate network services |
| `NUM_SERVICES` | `100` | Number of services to generate |

## API Access

Once the network simulator is running:
- **API Base URL**: `http://localhost:8003`
- **Health Check**: `http://localhost:8003/health`
- **API Documentation**: `http://localhost:8003/docs`
- **OpenAPI Spec**: `http://localhost:8003/openapi.json`

## Troubleshooting

### Common Issues

1. **Port 8003 Already in Use:**
   ```bash
   # macOS/Linux:
   lsof -i :8003
   kill -9 <PID>
   
   # Windows:
   netstat -ano | findstr :8003
   taskkill /PID <PID> /F
   ```

2. **DevContainer Won't Start:**
   - Ensure Docker Desktop is running
   - Try: "Dev Containers: Rebuild Container"
   - Check Docker has sufficient resources allocated

3. **Network Simulator Connection Errors:**
   ```bash
   # Check if simulator is running
   docker ps | grep network-simulator
   
   # View logs
   docker logs network-simulator
   ```

4. **Python Module Import Errors:**
   ```bash
   # Reinstall the client SDK
   cd net_agents
   pip install -e .
   ```

5. **Virtual Environment Issues:**
   ```bash
   # Deactivate current environment
   deactivate
   
   # Remove and recreate
   rm -rf venv  # or rmdir /s venv on Windows
   python -m venv venv
   
   # Reactivate and reinstall
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

### Platform-Specific Notes

**macOS:**
- May need to install Xcode command line tools: `xcode-select --install`
- If using M1/M2 Mac, Docker containers will run in emulation mode

**Linux:**
- May need to install additional packages: `sudo apt install build-essential python3-dev`
- Ensure your user is in the docker group: `sudo usermod -aG docker $USER`

**Windows:**
- PowerShell execution policy may need adjustment: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Consider using Windows Terminal for better command line experience
- WSL2 recommended for optimal Docker performance

### Getting Help

- Check the exercise guide: `net_agents/workshop/docs/EXERCISE_GUIDE.md`
- Review network reference: `net_agents/workshop/docs/NETWORK_REFERENCE.md`
- Setup instructions: `net_agents/workshop/docs/SETUP.md`

## Development

### Running Tests
```bash
cd net_agents
pytest
```

### Code Formatting
```bash
# If you want to format code (optional)
black net_agents/
ruff check net_agents/
```

## Architecture

- **Network Simulator**: FastAPI-based REST API simulating network infrastructure
- **Client SDK**: Python library for interacting with the network simulator
- **Workshop Exercises**: Progressive hands-on coding exercises
- **Docker Support**: Containerized deployment for consistency across environments

## Technologies Used

- Python 3.12
- FastAPI for the REST API
- SQLite for data persistence
- Pydantic for data validation
- HTTPX for HTTP client operations
- Docker for containerization
- VSCode DevContainers for development environment

## License

This workshop is part of the AutoCon project.

---

**Ready to start?** Open this repository in VSCode with the Dev Containers extension, or follow the setup instructions above. Begin with `ex0_verify_setup.py` to ensure everything is working correctly.