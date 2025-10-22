#!/usr/bin/env python3
"""
Simple script to run the Network Simulator FastAPI server.

Usage:
    python run_api.py

The API will be available at:
    - Swagger UI: http://localhost:8003/docs
    - ReDoc: http://localhost:8003/redoc
    - API Endpoints: http://localhost:8003/
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("Network Simulator API")
    print("=" * 70)
    print("\nStarting FastAPI server...")
    print("\nAPI Documentation:")
    print("  Swagger UI:  http://localhost:8003/docs")
    print("  ReDoc:       http://localhost:8003/redoc")
    print("\nEndpoints:")
    print("  Health:      GET  http://localhost:8003/health")
    print("  Nodes:       GET  http://localhost:8003/nodes")
    print("  Edges:       GET  http://localhost:8003/edges")
    print("  Analytics:   GET  http://localhost:8003/analytics/stats")
    print("\nPress CTRL+C to stop the server")
    print("=" * 70)
    print()

    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
