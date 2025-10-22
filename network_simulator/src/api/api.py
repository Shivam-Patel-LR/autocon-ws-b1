"""
FastAPI REST API for Network Simulator.
Provides CRUD operations for nodes, edges, and services with analytics endpoints.
"""

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
import uuid as uuid_module
import os

from database.database_manager import NetworkDatabase
from services.astar_router import AStarRouter
from api.api_models import (
    NodeCreate, NodeUpdate, NodeResponse,
    EdgeCreate, EdgeResponse, EdgeDetailResponse,
    ServiceCreate, ServiceResponse,
    EdgeUtilizationResponse, CapacityViolationResponse,
    DatabaseStatsResponse, HealthResponse, ErrorResponse,
    RouteRequest, RouteResponse, RouteNotFoundResponse
)


# ==================== Database Setup & Lifespan ====================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "network.db"
db: Optional[NetworkDatabase] = None


def get_db() -> NetworkDatabase:
    """
    Get database connection.

    Creates database if it doesn't exist (auto_init=True creates schema).
    """
    global db
    if db is None:
        db = NetworkDatabase(str(DB_PATH), auto_init=True)
    return db


def initialize_database_if_needed(db_instance: NetworkDatabase) -> None:
    """
    Initialize database with network data if it's empty.

    Checks if database has any nodes, and if not, generates a complete
    network topology with nodes, edges, and optional services.

    Args:
        db_instance: NetworkDatabase instance to initialize
    """
    # Check if database is empty
    stats = db_instance.get_stats()
    if stats['nodes'] > 0:
        print(f"Database already populated: {stats['nodes']} nodes, {stats['edges']} edges, {stats['services']} services")
        return

    # Check if auto-initialization is disabled
    auto_init = os.getenv('AUTO_INIT_DB', 'true').lower() == 'true'
    if not auto_init:
        print("Database is empty but AUTO_INIT_DB=false. Skipping initialization.")
        return

    print("\n" + "=" * 70)
    print("AUTO-INITIALIZING EMPTY DATABASE")
    print("=" * 70)

    try:
        # Import dependencies for initialization
        import uuid
        from core.config_loader import load_config
        from core.network_simulator import NetworkSimulator
        from utilities.dummy_network_generator import generate_and_save_dummy_network

        # Load configuration
        config = load_config()

        # Step 1: Ensure network elements CSV exists
        csv_path = Path(config.data_dir) / "network_elements.csv"
        num_nodes = int(os.getenv('INIT_NUM_NODES', 48))

        if not csv_path.exists():
            print(f"\nGenerating {num_nodes} network nodes...")
            generate_and_save_dummy_network(
                output_path=str(csv_path),
                num_nodes=num_nodes,
                seed=config.random_seed or 42
            )
        else:
            print(f"\nUsing existing network_elements.csv")

        # Step 2: Initialize simulator and build connections
        print("\nBuilding network topology...")
        simulator = NetworkSimulator(data_dir=config.data_dir)
        simulator.load_network_elements()

        print("\nBuilding connections (3-phase algorithm)...")
        simulator.build_connections(
            gamma=config.gamma,
            beta=config.beta,
            eta=config.eta,
            target_edges=config.target_edges,
            noise_factor=config.noise_factor,
            random_seed=config.random_seed,
            alpha_base_phase2=config.alpha_base_phase2,
            alpha_coefficient_phase2=config.alpha_coefficient_phase2,
            alpha_base_phase3=config.alpha_base_phase3,
            alpha_coefficient_phase3=config.alpha_coefficient_phase3,
            min_distance_threshold=config.min_distance_threshold,
            non_hub_threshold=config.non_hub_threshold,
            spokes_per_node=config.spokes_per_node,
            capacity_tolerance=config.capacity_tolerance,
        )

        # Step 3: Import nodes into database
        print("\nImporting nodes into database...")
        name_to_uuid = {}

        with db_instance.transaction():
            for name, element in simulator.network_elements.items():
                node_uuid = str(uuid.uuid4())
                name_to_uuid[name] = node_uuid

                db_instance.insert_node(
                    node_uuid=node_uuid,
                    name=element.name,
                    latitude=element.lat,
                    longitude=element.long,
                    vendor=element.vendor,
                    capacity_gbps=element.capacity_gbps
                )

        print(f"  Imported {len(name_to_uuid)} nodes")

        # Step 4: Import edges into database
        print("\nImporting edges into database...")
        edge_count = 0

        if simulator.connection_builder:
            with db_instance.transaction():
                for edge in simulator.connection_builder.edges:
                    source_uuid = name_to_uuid[edge['source']]
                    target_uuid = name_to_uuid[edge['target']]

                    # Ensure canonical ordering
                    if source_uuid > target_uuid:
                        source_uuid, target_uuid = target_uuid, source_uuid

                    edge_uuid = str(uuid.uuid4())

                    db_instance.insert_edge(
                        edge_uuid=edge_uuid,
                        node1_uuid=source_uuid,
                        node2_uuid=target_uuid,
                        capacity_gbps=edge['weight']
                    )
                    edge_count += 1

        print(f"  Imported {edge_count} edges")

        # Step 5: Generate services (optional)
        generate_services = os.getenv('INIT_GENERATE_SERVICES', 'true').lower() == 'true'
        if generate_services:
            print("\nGenerating services...")
            from services.generate_services_db import DatabaseServiceRouter

            router = DatabaseServiceRouter(
                db=db_instance,
                demand=config.demand_gbps,
                p_exponent=config.p_exponent,
                rho_exponent=config.rho_exponent,
                noise_delta=config.noise_delta,
                random_seed=config.service_random_seed or 42,
                enable_stage_a=config.enable_stage_a
            )

            num_services = int(os.getenv('INIT_NUM_SERVICES', config.target_services))
            service_count = router.generate_services(target_count=num_services)
            print(f"  Generated {service_count} services")
        else:
            print("\nSkipping service generation (INIT_GENERATE_SERVICES=false)")

        # Display final statistics
        final_stats = db_instance.get_stats()
        print("\n" + "=" * 70)
        print("AUTO-INITIALIZATION COMPLETE")
        print("=" * 70)
        print(f"Database populated with {final_stats['nodes']} nodes, {final_stats['edges']} edges, {final_stats['services']} services")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nWARNING: Database auto-initialization failed: {e}")
        print("API will start with empty database. You can populate it manually or via /container_init endpoint.")
        import traceback
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.

    Handles database initialization on startup and cleanup on shutdown.
    """
    global db

    # Startup: Initialize database connection
    print("\nStarting Network Simulator API...")
    db = NetworkDatabase(str(DB_PATH), auto_init=True)
    initialize_database_if_needed(db)
    print("API ready to serve requests\n")

    yield  # Application runs here

    # Shutdown: Clean up database connection
    if db:
        db.close()
        db = None


# ==================== FastAPI App Configuration ====================

app = FastAPI(
    title="Network Simulator API",
    description="""
    # Network Simulator REST API

    A comprehensive REST API for managing network topology data and analyzing network capacity.

    ## Overview

    This API provides full CRUD operations for a simulated network infrastructure consisting of:
    - **48 Network Nodes** across the eastern United States
    - **200+ Network Connections** with capacity constraints
    - **100+ Routed Services** with path tracking

    ## Features

    ### Node Management
    Create, read, update, and delete network elements with geographic coordinates, vendor information, and capacity specifications.

    ### Edge Management
    Manage bidirectional connections between nodes with capacity constraints and utilization tracking.

    ### Analytics & Capacity
    Query capacity utilization, identify bottlenecks, and analyze network statistics in real-time.

    ### Advanced Filtering
    Filter nodes by vendor and minimum capacity. Query edges by endpoints. Track services by node or edge usage.

    ## Data Model

    - **UUIDs**: All entities use UUID-based identifiers for referential integrity
    - **SQLite Database**: Single source of truth with ACID guarantees
    - **Capacity Tracking**: Pre-computed utilization metrics for performance
    - **Path Validation**: All service paths are validated for connectivity

    ## Getting Started

    1. **Health Check**: `GET /health` - Verify API and database connectivity
    2. **List Nodes**: `GET /nodes` - View all network elements
    3. **View Statistics**: `GET /analytics/stats` - Get network overview
    4. **Explore**: Use the interactive endpoints below to test the API

    ## Support

    - **Interactive Documentation** - You are here!
    - **[Alternative Docs](/redoc)** - Clean, scrollable documentation
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Network Simulator Support",
    },
    license_info={
        "name": "Educational Use",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "**Health Check** - Verify API and database status before making requests"
        },
        {
            "name": "nodes",
            "description": "**Network Nodes** - Manage network elements with geographic locations, vendor info, and capacity specs"
        },
        {
            "name": "edges",
            "description": "**Network Edges** - Manage connections between nodes with capacity constraints and bi-directional links"
        },
        {
            "name": "services",
            "description": "**Network Services** - Route services through the network with multi-hop path tracking and capacity allocation"
        },
        {
            "name": "analytics",
            "description": "**Analytics** - Query capacity utilization, network statistics, and identify bottlenecks"
        },
        {
            "name": "routing",
            "description": "**Routing** - Compute shortest paths between nodes using A* algorithm with capacity constraints"
        }
    ],
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Endpoint ====================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check API and database health status"
)
async def health_check():
    """Health check endpoint."""
    try:
        db_instance = get_db()
        # Simple query to verify database is accessible
        stats = db_instance.get_stats()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    )


# ==================== Node Endpoints ====================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth.

    Uses the Haversine formula for accurate distance calculation.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, asin, sqrt

    R = 6371  # Earth's radius in kilometers

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return R * c


@app.get(
    "/nodes",
    response_model=List[NodeResponse],
    tags=["nodes"],
    summary="List all nodes",
    description="""
    Get a list of all network nodes with optional filtering.

    **Capacity Filters:**
    - `min_total_capacity` / `max_total_capacity`: Filter by total node capacity range
    - `min_free_capacity`: Filter by available (unused) capacity

    **Geographic Filter:**
    - Requires all three: `latitude`, `longitude`, `max_distance_km`
    - Returns only nodes within the specified distance from the reference point

    **Vendor Filter:**
    - `vendor`: Filter by exact vendor name match
    """
)
async def get_nodes(
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    min_total_capacity: Optional[float] = Query(None, description="Minimum total capacity in Gbps"),
    max_total_capacity: Optional[float] = Query(None, description="Maximum total capacity in Gbps"),
    min_free_capacity: Optional[float] = Query(None, description="Minimum free (unused) capacity in Gbps"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Reference latitude for geographic search"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Reference longitude for geographic search"),
    max_distance_km: Optional[float] = Query(None, gt=0, description="Maximum distance from reference point in km")
):
    """Get all nodes with utilization data, optionally filtered."""
    db_instance = get_db()
    nodes = db_instance.get_all_nodes_with_utilization()

    # Apply vendor filter
    if vendor:
        nodes = [n for n in nodes if n['vendor'] == vendor]

    # Apply total capacity range filter
    if min_total_capacity is not None:
        nodes = [n for n in nodes if n['capacity_gbps'] >= min_total_capacity]
    if max_total_capacity is not None:
        nodes = [n for n in nodes if n['capacity_gbps'] <= max_total_capacity]

    # Apply free capacity filter
    if min_free_capacity is not None:
        nodes = [n for n in nodes if n['free_capacity_gbps'] >= min_free_capacity]

    # Apply geographic filter (requires all three parameters)
    if latitude is not None and longitude is not None and max_distance_km is not None:
        filtered_nodes = []
        for node in nodes:
            distance = haversine_distance(latitude, longitude, node['latitude'], node['longitude'])
            if distance <= max_distance_km:
                filtered_nodes.append(node)
        nodes = filtered_nodes
    elif any(param is not None for param in [latitude, longitude, max_distance_km]):
        # If some but not all geographic params provided, raise error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geographic filtering requires all three parameters: latitude, longitude, and max_distance_km"
        )

    return [NodeResponse(**node) for node in nodes]


@app.get(
    "/nodes/{node_uuid}",
    response_model=NodeResponse,
    tags=["nodes"],
    summary="Get node by UUID",
    description="Retrieve a specific node by its UUID",
    responses={404: {"model": ErrorResponse, "description": "Node not found"}}
)
async def get_node(node_uuid: str):
    """Get a node by UUID."""
    db_instance = get_db()
    node = db_instance.get_node_by_uuid(node_uuid)

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {node_uuid} not found"
        )

    # Calculate free capacity
    utilizations = db_instance.get_node_utilizations()
    used_capacity = utilizations.get(node_uuid, 0.0)
    node['free_capacity_gbps'] = max(0.0, node['capacity_gbps'] - used_capacity)

    return NodeResponse(**node)


@app.get(
    "/nodes/by-name/{name_substring}",
    response_model=List[NodeResponse],
    tags=["nodes"],
    summary="Search nodes by name",
    description="""
    Search for nodes by name substring (case-insensitive).

    Returns all nodes where the name contains the given substring.
    Returns empty list if no matches found.

    Examples:
    - `/nodes/by-name/New` → Returns nodes like "New York-NY", "Newark-NJ"
    - `/nodes/by-name/boston` → Returns "Boston-MA" (case-insensitive)
    - `/nodes/by-name/Downtown` → Returns all nodes with "Downtown" in name
    """
)
async def search_nodes_by_name(name_substring: str):
    """Search for nodes by name substring."""
    db_instance = get_db()
    nodes = db_instance.search_nodes_by_name(name_substring)

    # Calculate free capacity for all matched nodes
    utilizations = db_instance.get_node_utilizations()
    for node in nodes:
        used_capacity = utilizations.get(node['uuid'], 0.0)
        node['free_capacity_gbps'] = max(0.0, node['capacity_gbps'] - used_capacity)

    return [NodeResponse(**node) for node in nodes]


@app.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["nodes"],
    summary="Create a new node",
    description="Create a new network node with auto-generated UUID",
    responses={400: {"model": ErrorResponse, "description": "Invalid input or duplicate name"}}
)
async def create_node(node: NodeCreate):
    """Create a new node."""
    db_instance = get_db()

    # Check if name already exists
    existing = db_instance.get_node_by_name(node.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node with name '{node.name}' already exists"
        )

    # Generate UUID
    node_uuid = str(uuid_module.uuid4())

    try:
        db_instance.insert_node(
            node_uuid=node_uuid,
            name=node.name,
            latitude=node.latitude,
            longitude=node.longitude,
            vendor=node.vendor,
            capacity_gbps=node.capacity_gbps
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create node: {str(e)}"
        )

    # Retrieve and return the created node
    created_node = db_instance.get_node_by_uuid(node_uuid)
    # Calculate free capacity (will be same as total since new node has no services)
    created_node['free_capacity_gbps'] = created_node['capacity_gbps']
    return NodeResponse(**created_node)


@app.put(
    "/nodes/{node_uuid}",
    response_model=NodeResponse,
    tags=["nodes"],
    summary="Update a node",
    description="Update an existing node's attributes",
    responses={404: {"model": ErrorResponse, "description": "Node not found"}}
)
async def update_node(node_uuid: str, node_update: NodeUpdate):
    """Update a node."""
    db_instance = get_db()

    # Check if node exists
    existing = db_instance.get_node_by_uuid(node_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {node_uuid} not found"
        )

    # Build update query
    updates = {}
    if node_update.name is not None:
        updates['name'] = node_update.name
    if node_update.latitude is not None:
        updates['latitude'] = node_update.latitude
    if node_update.longitude is not None:
        updates['longitude'] = node_update.longitude
    if node_update.vendor is not None:
        updates['vendor'] = node_update.vendor
    if node_update.capacity_gbps is not None:
        updates['capacity_gbps'] = node_update.capacity_gbps

    if not updates:
        # No updates provided, return existing node
        # Calculate free capacity
        utilizations = db_instance.get_node_utilizations()
        used_capacity = utilizations.get(node_uuid, 0.0)
        existing['free_capacity_gbps'] = max(0.0, existing['capacity_gbps'] - used_capacity)
        return NodeResponse(**existing)

    # Perform update
    cursor = db_instance.conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    set_clause += ", updated_at = CURRENT_TIMESTAMP"
    values = list(updates.values()) + [node_uuid]

    try:
        cursor.execute(f"UPDATE nodes SET {set_clause} WHERE uuid = ?", values)
        db_instance.conn.commit()
    except Exception as e:
        db_instance.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update node: {str(e)}"
        )
    finally:
        cursor.close()

    # Return updated node
    updated_node = db_instance.get_node_by_uuid(node_uuid)
    # Calculate free capacity
    utilizations = db_instance.get_node_utilizations()
    used_capacity = utilizations.get(node_uuid, 0.0)
    updated_node['free_capacity_gbps'] = max(0.0, updated_node['capacity_gbps'] - used_capacity)
    return NodeResponse(**updated_node)


@app.delete(
    "/nodes/{node_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["nodes"],
    summary="Delete a node",
    description="Delete a node (only if not referenced by edges or services)",
    responses={
        404: {"model": ErrorResponse, "description": "Node not found"},
        409: {"model": ErrorResponse, "description": "Node is referenced by edges or services"}
    }
)
async def delete_node(node_uuid: str):
    """Delete a node."""
    db_instance = get_db()

    # Check if node exists
    existing = db_instance.get_node_by_uuid(node_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {node_uuid} not found"
        )

    # Try to delete
    cursor = db_instance.conn.cursor()
    try:
        cursor.execute("DELETE FROM nodes WHERE uuid = ?", (node_uuid,))
        db_instance.conn.commit()
    except Exception as e:
        db_instance.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete node: {str(e)}. It may be referenced by edges or services."
        )
    finally:
        cursor.close()

    return None


# ==================== Edge Endpoints ====================

@app.get(
    "/edges",
    response_model=List[EdgeResponse],
    tags=["edges"],
    summary="List all edges",
    description="Get a list of all network edges (connections)"
)
async def get_edges():
    """Get all edges."""
    db_instance = get_db()
    edges = db_instance.get_all_edges()
    return [EdgeResponse(**edge) for edge in edges]


@app.get(
    "/edges/{edge_uuid}",
    response_model=EdgeResponse,
    tags=["edges"],
    summary="Get edge by UUID",
    description="Retrieve a specific edge by its UUID",
    responses={404: {"model": ErrorResponse, "description": "Edge not found"}}
)
async def get_edge(edge_uuid: str):
    """Get an edge by UUID."""
    db_instance = get_db()
    edge = db_instance.get_edge_by_uuid(edge_uuid)

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge with UUID {edge_uuid} not found"
        )

    return EdgeResponse(**edge)


@app.get(
    "/edges/by-endpoints/",
    response_model=EdgeResponse,
    tags=["edges"],
    summary="Get edge by node endpoints",
    description="Retrieve an edge by its two endpoint node UUIDs",
    responses={404: {"model": ErrorResponse, "description": "Edge not found"}}
)
async def get_edge_by_endpoints(
    node1_uuid: str = Query(..., description="First node UUID"),
    node2_uuid: str = Query(..., description="Second node UUID")
):
    """Get an edge by its endpoint nodes."""
    db_instance = get_db()
    edge = db_instance.get_edge_by_endpoints(node1_uuid, node2_uuid)

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge between nodes {node1_uuid} and {node2_uuid} not found"
        )

    return EdgeResponse(**edge)


@app.post(
    "/edges",
    response_model=EdgeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["edges"],
    summary="Create a new edge",
    description="Create a new edge between two nodes with auto-generated UUID",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or duplicate edge"},
        404: {"model": ErrorResponse, "description": "One or both nodes not found"}
    }
)
async def create_edge(edge: EdgeCreate):
    """Create a new edge."""
    db_instance = get_db()

    # Verify both nodes exist
    node1 = db_instance.get_node_by_uuid(edge.node1_uuid)
    node2 = db_instance.get_node_by_uuid(edge.node2_uuid)

    if not node1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {edge.node1_uuid} not found"
        )
    if not node2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {edge.node2_uuid} not found"
        )

    # Check for duplicate edge
    existing = db_instance.get_edge_by_endpoints(edge.node1_uuid, edge.node2_uuid)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Edge between these nodes already exists"
        )

    # Generate UUID
    edge_uuid = str(uuid_module.uuid4())

    try:
        db_instance.insert_edge(
            edge_uuid=edge_uuid,
            node1_uuid=edge.node1_uuid,
            node2_uuid=edge.node2_uuid,
            capacity_gbps=edge.capacity_gbps
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create edge: {str(e)}"
        )

    # Retrieve and return the created edge
    created_edge = db_instance.get_edge_by_uuid(edge_uuid)
    return EdgeResponse(**created_edge)


@app.delete(
    "/edges/{edge_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["edges"],
    summary="Delete an edge",
    description="Delete an edge (only if not referenced by services)",
    responses={
        404: {"model": ErrorResponse, "description": "Edge not found"},
        409: {"model": ErrorResponse, "description": "Edge is referenced by services"}
    }
)
async def delete_edge(edge_uuid: str):
    """Delete an edge."""
    db_instance = get_db()

    # Check if edge exists
    existing = db_instance.get_edge_by_uuid(edge_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge with UUID {edge_uuid} not found"
        )

    # Try to delete
    cursor = db_instance.conn.cursor()
    try:
        cursor.execute("DELETE FROM edges WHERE uuid = ?", (edge_uuid,))
        db_instance.conn.commit()
    except Exception as e:
        db_instance.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete edge: {str(e)}. It may be referenced by services."
        )
    finally:
        cursor.close()

    return None


# ==================== Analytics Endpoints ====================

@app.get(
    "/analytics/stats",
    response_model=DatabaseStatsResponse,
    tags=["analytics"],
    summary="Get database statistics",
    description="Get counts of nodes, edges, and services in the database"
)
async def get_stats():
    """Get database statistics."""
    db_instance = get_db()
    stats = db_instance.get_stats()
    return DatabaseStatsResponse(**stats)


@app.get(
    "/capacity/summary",
    response_model=List[EdgeUtilizationResponse],
    tags=["analytics"],
    summary="Get capacity utilization summary",
    description="Get capacity utilization for all edges, sorted by utilization percentage"
)
async def get_capacity_summary():
    """Get capacity utilization for all edges."""
    db_instance = get_db()
    utilizations = db_instance.get_all_edge_utilizations()
    return [EdgeUtilizationResponse(**util) for util in utilizations]


@app.get(
    "/capacity/edge/{edge_uuid}",
    response_model=EdgeUtilizationResponse,
    tags=["analytics"],
    summary="Get edge capacity utilization",
    description="Get capacity utilization stats for a specific edge",
    responses={404: {"model": ErrorResponse, "description": "Edge not found"}}
)
async def get_edge_capacity(edge_uuid: str):
    """Get capacity utilization for a specific edge."""
    db_instance = get_db()

    # Verify edge exists
    edge = db_instance.get_edge_by_uuid(edge_uuid)
    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge with UUID {edge_uuid} not found"
        )

    utilization = db_instance.get_edge_utilization(edge_uuid)
    return EdgeUtilizationResponse(**utilization)


@app.get(
    "/capacity/violations",
    response_model=List[CapacityViolationResponse],
    tags=["analytics"],
    summary="Get capacity violations",
    description="Get all edges where demand exceeds capacity"
)
async def get_capacity_violations():
    """Get all capacity violations."""
    db_instance = get_db()
    violations = db_instance.verify_capacity_constraints()
    return [CapacityViolationResponse(**violation) for violation in violations]


# ==================== Service Endpoints ====================

@app.get(
    "/services",
    response_model=List[ServiceResponse],
    tags=["services"],
    summary="List all services",
    description="Get a list of all network services with their paths"
)
async def get_services(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of services to return")
):
    """Get all services."""
    db_instance = get_db()
    services = db_instance.get_all_services()

    # Apply limit if specified
    if limit:
        services = services[:limit]

    return [ServiceResponse(**service) for service in services]


@app.get(
    "/services/{service_uuid}",
    response_model=ServiceResponse,
    tags=["services"],
    summary="Get service by UUID",
    description="Retrieve a specific service with its complete path information",
    responses={404: {"model": ErrorResponse, "description": "Service not found"}}
)
async def get_service(service_uuid: str):
    """Get a service by UUID."""
    db_instance = get_db()
    service = db_instance.get_service_by_uuid(service_uuid)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with UUID {service_uuid} not found"
        )

    return ServiceResponse(**service)


@app.post(
    "/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["services"],
    summary="Create a new service",
    description="Create a new routed service with path tracking and auto-generated UUID",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or validation error"},
        404: {"model": ErrorResponse, "description": "Referenced nodes or edges not found"}
    }
)
async def create_service(service: ServiceCreate):
    """Create a new service with path."""
    db_instance = get_db()

    # Verify source and destination nodes exist
    source_node = db_instance.get_node_by_uuid(service.source_node_uuid)
    dest_node = db_instance.get_node_by_uuid(service.destination_node_uuid)

    if not source_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source node with UUID {service.source_node_uuid} not found"
        )
    if not dest_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination node with UUID {service.destination_node_uuid} not found"
        )

    # Verify all path nodes exist
    for node_uuid in service.path_node_uuids:
        node = db_instance.get_node_by_uuid(node_uuid)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path node with UUID {node_uuid} not found"
            )

    # Verify all path edges exist
    for edge_uuid in service.path_edge_uuids:
        edge = db_instance.get_edge_by_uuid(edge_uuid)
        if not edge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path edge with UUID {edge_uuid} not found"
            )

    # Validate path consistency
    if service.path_node_uuids[0] != service.source_node_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First node in path must match source_node_uuid"
        )
    if service.path_node_uuids[-1] != service.destination_node_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Last node in path must match destination_node_uuid"
        )

    # Compute total_distance_km from path edges
    total_distance_km = 0.0
    for edge_uuid in service.path_edge_uuids:
        edge = db_instance.get_edge_by_uuid(edge_uuid)
        # Get both nodes for this edge
        node1 = db_instance.get_node_by_uuid(edge['node1_uuid'])
        node2 = db_instance.get_node_by_uuid(edge['node2_uuid'])
        # Calculate haversine distance
        edge_distance = haversine_distance(
            node1['latitude'], node1['longitude'],
            node2['latitude'], node2['longitude']
        )
        total_distance_km += edge_distance

    # Generate UUID
    service_uuid = str(uuid_module.uuid4())
    hop_count = len(service.path_node_uuids) - 1

    try:
        db_instance.insert_service_with_path(
            service_uuid=service_uuid,
            name=service.name,
            source_node_uuid=service.source_node_uuid,
            destination_node_uuid=service.destination_node_uuid,
            demand_gbps=service.demand_gbps,
            hop_count=hop_count,
            total_distance_km=total_distance_km,
            service_timestamp=service.service_timestamp,
            path_node_uuids=service.path_node_uuids,
            path_edge_uuids=service.path_edge_uuids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create service: {str(e)}"
        )

    # Retrieve and return the created service
    created_service = db_instance.get_service_by_uuid(service_uuid)
    return ServiceResponse(**created_service)


@app.delete(
    "/services/{service_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["services"],
    summary="Delete a service",
    description="Delete a service and free up capacity on its path edges",
    responses={404: {"model": ErrorResponse, "description": "Service not found"}}
)
async def delete_service(service_uuid: str):
    """Delete a service."""
    db_instance = get_db()

    # Check if service exists
    existing = db_instance.get_service_by_uuid(service_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with UUID {service_uuid} not found"
        )

    # Delete the service (CASCADE will handle path tables)
    cursor = db_instance.conn.cursor()
    try:
        # Get demand before deleting
        demand = existing['demand_gbps']
        path_edges = existing['path_edge_uuids']

        # Delete service
        cursor.execute("DELETE FROM services WHERE uuid = ?", (service_uuid,))

        # Update capacity utilization for affected edges
        for edge_uuid in path_edges:
            cursor.execute("""
                UPDATE capacity_utilization
                SET total_demand_gbps = total_demand_gbps - ?,
                    service_count = service_count - 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE edge_uuid = ?
            """, (demand, edge_uuid))

        db_instance.conn.commit()
    except Exception as e:
        db_instance.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete service: {str(e)}"
        )
    finally:
        cursor.close()

    return None


@app.get(
    "/services/by-node/{node_uuid}",
    response_model=List[ServiceResponse],
    tags=["services"],
    summary="Get services by node",
    description="Get all services originating from a specific node",
    responses={404: {"model": ErrorResponse, "description": "Node not found"}}
)
async def get_services_by_node(node_uuid: str):
    """Get all services originating from a specific node."""
    db_instance = get_db()

    # Verify node exists
    node = db_instance.get_node_by_uuid(node_uuid)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with UUID {node_uuid} not found"
        )

    # Get services from node (basic info only)
    services = db_instance.get_services_from_node(node_uuid)

    # For each service, get full path information
    full_services = []
    for svc in services:
        full_service = db_instance.get_service_by_uuid(svc['uuid'])
        if full_service:
            full_services.append(ServiceResponse(**full_service))

    return full_services


@app.get(
    "/services/by-edge/{edge_uuid}",
    response_model=List[ServiceResponse],
    tags=["services"],
    summary="Get services by edge",
    description="Get all services that traverse a specific edge",
    responses={404: {"model": ErrorResponse, "description": "Edge not found"}}
)
async def get_services_by_edge(edge_uuid: str):
    """Get all services using a specific edge."""
    db_instance = get_db()

    # Verify edge exists
    edge = db_instance.get_edge_by_uuid(edge_uuid)
    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge with UUID {edge_uuid} not found"
        )

    # Get services using this edge
    services = db_instance.get_services_using_edge(edge_uuid)

    # For each service, get full path information
    full_services = []
    for svc in services:
        full_service = db_instance.get_service_by_uuid(svc['uuid'])
        if full_service:
            full_services.append(ServiceResponse(**full_service))

    return full_services


# ==================== Routing Endpoints ====================

@app.post(
    "/routing/astar",
    response_model=RouteResponse,
    tags=["routing"],
    summary="Compute shortest path with A* algorithm",
    description="""
    Compute the shortest geographic path between two nodes using A* search algorithm.

    **Algorithm Details:**
    - Uses Haversine distance as both cost (actual) and heuristic (estimate)
    - Capacity acts as a hard constraint: only traverses edges with sufficient capacity
    - Finds the shortest distance path, not necessarily the minimum hop count

    **Parameters:**
    - source_node_uuid: Starting node UUID
    - destination_node_uuid: Target node UUID
    - demand_gbps: Required bandwidth (default: 5.0 Gbps)

    **Returns 422 if:**
    - No path exists between nodes
    - No path has sufficient capacity for the requested demand
    """,
    responses={
        404: {"model": ErrorResponse, "description": "Source or destination node not found"},
        422: {"model": RouteNotFoundResponse, "description": "No feasible route found"}
    }
)
async def compute_route_astar(route_request: RouteRequest):
    """Compute shortest path using A* with capacity constraints."""
    db_instance = get_db()

    # Verify source and destination nodes exist
    source_node = db_instance.get_node_by_uuid(route_request.source_node_uuid)
    if not source_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source node with UUID {route_request.source_node_uuid} not found"
        )

    dest_node = db_instance.get_node_by_uuid(route_request.destination_node_uuid)
    if not dest_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination node with UUID {route_request.destination_node_uuid} not found"
        )

    # Build network graph and get current state
    graph = db_instance.build_network_graph()
    residual_capacities = db_instance.get_residual_capacities()
    node_coordinates = db_instance.get_node_coordinates_dict()

    # Initialize A* router
    router = AStarRouter(node_coordinates)

    # Compute route
    route = router.compute_route(
        graph=graph,
        source_uuid=route_request.source_node_uuid,
        destination_uuid=route_request.destination_node_uuid,
        residual_capacities=residual_capacities,
        demand_gbps=route_request.demand_gbps
    )

    if route is None:
        # No route found - return 422 with details
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "source_node_uuid": route_request.source_node_uuid,
                "destination_node_uuid": route_request.destination_node_uuid,
                "demand_gbps": route_request.demand_gbps,
                "error": "No feasible route found",
                "reason": f"No path exists with sufficient capacity for demand of {route_request.demand_gbps} Gbps"
            }
        )

    # Return successful route
    return RouteResponse(
        source_node_uuid=route_request.source_node_uuid,
        destination_node_uuid=route_request.destination_node_uuid,
        path_node_uuids=route['path_node_uuids'],
        path_edge_uuids=route['path_edge_uuids'],
        total_distance_km=route['total_distance_km'],
        hop_count=route['hop_count'],
        min_available_capacity=route['min_available_capacity'],
        computation_time_ms=route['computation_time_ms'],
        demand_gbps=route_request.demand_gbps
    )


@app.get(
    "/routing/astar",
    response_model=RouteResponse,
    tags=["routing"],
    summary="Compute shortest path (GET with query params)",
    description="""
    Compute shortest path using A* algorithm via GET request with query parameters.
    Convenient for simple testing and URL-based routing requests.

    For detailed documentation, see POST /routing/astar
    """,
    responses={
        404: {"model": ErrorResponse, "description": "Source or destination node not found"},
        422: {"model": RouteNotFoundResponse, "description": "No feasible route found"}
    }
)
async def compute_route_astar_get(
    source_node_uuid: str = Query(..., description="Source node UUID"),
    destination_node_uuid: str = Query(..., description="Destination node UUID"),
    demand_gbps: float = Query(5.0, gt=0, description="Required bandwidth in Gbps")
):
    """Compute shortest path using A* (GET method)."""
    # Delegate to POST handler
    route_request = RouteRequest(
        source_node_uuid=source_node_uuid,
        destination_node_uuid=destination_node_uuid,
        demand_gbps=demand_gbps
    )
    return await compute_route_astar(route_request)
