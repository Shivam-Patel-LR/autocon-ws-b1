# Building AI Agents for Smarter Networks - Workshop Materials

Welcome to the AI Agents workshop! This directory contains all materials for learning to build intelligent network management agents using the OpenAI Agents SDK.

## Quick Start

1. **Setup Environment**: Follow [SETUP.md](SETUP.md)
2. **Review Network Basics**: Read [NETWORK_REFERENCE.md](NETWORK_REFERENCE.md)
3. **Start Exercises**: Work through [EXERCISE_GUIDE.md](EXERCISE_GUIDE.md)
4. **Run Support Agent**: `python ex1_support_agent.py` for help

## Workshop Structure

### Documentation

- **SETUP.md** - Installation and configuration guide
- **NETWORK_REFERENCE.md** - Quick reference for network simulator API
- **EXERCISE_GUIDE.md** - Complete workshop exercises (9 exercises)
- **README.md** - This file

### Working Code

- **ex1_support_agent.py** - Fully functional support agent
- **ex0_verify_setup.py** - Setup verification script

### Solutions

Reference implementations in `solutions/` (for instructors)

## Workshop Exercises

1. **Generative AI Frameworks** - Compare LangChain vs OpenAI Agents SDK
2. **Agentic Design Patterns** - Centralized vs decentralized architectures
3. **Segmentation of Responsibilities** - Divide agent duties effectively
4. **Build Support Agent** - Create tool-less conversational agent
5. **Network Problem Introduction** - Understand the topology
6. **Build Planning Agent** - Find routes with capacity constraints
7. **Build Provisioning Agent** - Create services on the network
8. **Iterative Improvement** - Refine prompts and error handling
9. **Full Workflow Example** - Integrate all agents end-to-end

## Key Technologies

- **OpenAI Agents SDK** - https://openai.github.io/openai-agents-python/
- **Network Simulator Client** - Python SDK for network API
- **FastAPI** - Network simulator REST API
- **Docker** - Container for running the simulator

## Prerequisites

- Python 3.12
- OpenAI API key (will be provided)
- Basic Python programming knowledge
- Understanding of REST APIs (helpful)

## Getting Help

1. **Run the support agent**: `python support_agent.py`
2. **Check documentation**: SETUP.md, NETWORK_REFERENCE.md, EXERCISE_GUIDE.md
3. **Review solutions**: Compare your code to solutions/ directory
4. **Ask instructors**: During workshop sessions

## Files Overview

```
workshop/
├── README.md                          # This file
├── SETUP.md                           # Setup instructions
├── NETWORK_REFERENCE.md               # API quick reference
├── EXERCISE_GUIDE.md                  # All 9 exercises
├── support_agent.py                   # Working support agent
├── verify_setup.py                    # Setup verification
├── .env.example                       # Environment template
├── templates/                         # Exercise starter code
│   ├── planning_agent_starter.py
│   └── provisioning_agent_starter.py
└── solutions/                         # Reference implementations
```

## Tips for Success

1. Read the docs first - SETUP.md and NETWORK_REFERENCE.md
2. Run verify_setup.py to ensure everything works
3. Use the support agent for help
4. Test incrementally - test each tool as you build it
5. Read error messages carefully
6. Ask for help if stuck

## Common Issues

| Issue                  | Solution                                                                    |
| ---------------------- | --------------------------------------------------------------------------- |
| API won't connect      | Start simulator: `docker compose up -d`                                     |
| No API key             | Create `.env` file with the variables in `net_agents/workshop/.env.example` |
| Import errors          | Install SDK: `uv pip install openai-agents`                                 |
| Agent won't call tools | Check tool docstrings are clear                                             |

## Next Steps After Workshop

- Build more specialized agents (monitoring, optimization)
- Explore async agents for parallel operations
- Add agent memory and learning capabilities
- Build your own agent framework
- Contribute improvements back to the community

## Resources

- **OpenAI Agents SDK**: https://openai.github.io/openai-agents-python/
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Network Simulator**: http://localhost:8003/docs (when running)
- **SDK Documentation**: ../README.md

## License

Educational use only.

---

Ready to start? Read [SETUP.md](SETUP.md) first.
