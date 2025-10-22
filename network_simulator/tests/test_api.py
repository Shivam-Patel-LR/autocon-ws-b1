"""
Comprehensive test suite for Network Simulator API.
Tests all endpoints with various scenarios including error cases.
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import uuid as uuid_module
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.api import app, DB_PATH
from database.database_manager import NetworkDatabase


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()

    # Initialize database with schema
    db = NetworkDatabase(temp_db_path)

    # Add sample nodes
    node1_uuid = str(uuid_module.uuid4())
    node2_uuid = str(uuid_module.uuid4())
    node3_uuid = str(uuid_module.uuid4())

    db.insert_node(node1_uuid, "NYC-Manhattan", 40.7589, -73.9851, "TeleConnect", 5000.0)
    db.insert_node(node2_uuid, "Boston-Downtown", 42.3601, -71.0589, "NetWorks", 3000.0)
    db.insert_node(node3_uuid, "Philadelphia-Center", 39.9526, -75.1652, "LinkSystems", 2500.0)

    # Add sample edges
    edge1_uuid = str(uuid_module.uuid4())
    edge2_uuid = str(uuid_module.uuid4())

    db.insert_edge(edge1_uuid, node1_uuid, node2_uuid, 100.0)
    db.insert_edge(edge2_uuid, node2_uuid, node3_uuid, 75.0)

    yield {
        'db': db,
        'db_path': temp_db_path,
        'node1_uuid': node1_uuid,
        'node2_uuid': node2_uuid,
        'node3_uuid': node3_uuid,
        'edge1_uuid': edge1_uuid,
        'edge2_uuid': edge2_uuid
    }

    # Cleanup
    db.close()
    try:
        os.unlink(temp_db_path)
    except:
        pass


@pytest.fixture
def client(test_db, monkeypatch):
    """Create test client with mocked database."""
    # Mock the DB_PATH and get_db function
    import api.api as api_module
    monkeypatch.setattr(api_module, "DB_PATH", Path(test_db['db_path']))
    monkeypatch.setattr(api_module, "db", test_db['db'])

    with TestClient(app) as tc:
        yield tc


# ==================== Health Endpoint Tests ====================

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


# ==================== Node Endpoint Tests ====================

def test_get_all_nodes(client, test_db):
    """Test getting all nodes."""
    response = client.get("/nodes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] in ["NYC-Manhattan", "Boston-Downtown", "Philadelphia-Center"]


def test_get_nodes_with_vendor_filter(client, test_db):
    """Test getting nodes filtered by vendor."""
    response = client.get("/nodes?vendor=TeleConnect")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "NYC-Manhattan"
    assert data[0]["vendor"] == "TeleConnect"


def test_get_nodes_with_capacity_filter(client, test_db):
    """Test getting nodes filtered by minimum capacity."""
    response = client.get("/nodes?min_total_capacity=3500")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["capacity_gbps"] >= 3500
    assert "free_capacity_gbps" in data[0]


def test_get_node_by_uuid(client, test_db):
    """Test getting a specific node by UUID."""
    node_uuid = test_db['node1_uuid']
    response = client.get(f"/nodes/{node_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == node_uuid
    assert data["name"] == "NYC-Manhattan"
    assert data["capacity_gbps"] == 5000.0


def test_get_node_by_uuid_not_found(client):
    """Test getting a node with invalid UUID."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/nodes/{fake_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_node_by_name(client, test_db):
    """Test searching for nodes by exact name."""
    response = client.get("/nodes/by-name/Boston-Downtown")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Boston-Downtown"
    assert data[0]["uuid"] == test_db['node2_uuid']
    assert "free_capacity_gbps" in data[0]


def test_get_node_by_name_not_found(client):
    """Test searching for node with non-existent name returns empty list."""
    response = client.get("/nodes/by-name/NonExistent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_nodes_by_name_substring(client, test_db):
    """Test substring search returns multiple matching nodes."""
    # Search for "Downtown" - should match "Boston-Downtown"
    response = client.get("/nodes/by-name/Downtown")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify all results contain "Downtown" in name
    for node in data:
        assert "Downtown" in node["name"]
        assert "free_capacity_gbps" in node


def test_search_nodes_by_name_case_insensitive(client, test_db):
    """Test that name search is case-insensitive."""
    # Search for "boston" (lowercase) should match "Boston-Downtown"
    response = client.get("/nodes/by-name/boston")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify Boston-Downtown is in results
    boston_found = any("Boston" in node["name"] for node in data)
    assert boston_found


def test_search_nodes_by_name_multiple_results(client, test_db):
    """Test substring search returning multiple results."""
    # Create additional nodes with similar names for better testing
    new_node1 = {
        "name": "New York-Manhattan",
        "latitude": 40.7831,
        "longitude": -73.9712,
        "vendor": "TeleConnect",
        "capacity_gbps": 6000.0
    }
    new_node2 = {
        "name": "New Haven-CT",
        "latitude": 41.3083,
        "longitude": -72.9279,
        "vendor": "NetWorks",
        "capacity_gbps": 2000.0
    }
    client.post("/nodes", json=new_node1)
    client.post("/nodes", json=new_node2)

    # Search for "New" should return multiple nodes
    response = client.get("/nodes/by-name/New")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least New York-Manhattan and New Haven-CT
    # Verify all contain "New"
    for node in data:
        assert "New" in node["name"]


def test_create_node(client):
    """Test creating a new node."""
    new_node = {
        "name": "Chicago-Loop",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "vendor": "TeleConnect",
        "capacity_gbps": 4000.0
    }
    response = client.post("/nodes", json=new_node)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Chicago-Loop"
    assert "uuid" in data
    assert data["capacity_gbps"] == 4000.0


def test_create_node_duplicate_name(client, test_db):
    """Test creating a node with duplicate name."""
    duplicate_node = {
        "name": "NYC-Manhattan",  # Already exists
        "latitude": 40.7589,
        "longitude": -73.9851,
        "vendor": "TeleConnect",
        "capacity_gbps": 5000.0
    }
    response = client.post("/nodes", json=duplicate_node)
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


def test_update_node(client, test_db):
    """Test updating a node."""
    node_uuid = test_db['node1_uuid']
    update_data = {
        "capacity_gbps": 6000.0,
        "vendor": "NewVendor"
    }
    response = client.put(f"/nodes/{node_uuid}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["capacity_gbps"] == 6000.0
    assert data["vendor"] == "NewVendor"
    assert data["name"] == "NYC-Manhattan"  # Unchanged


def test_update_node_not_found(client):
    """Test updating a non-existent node."""
    fake_uuid = str(uuid_module.uuid4())
    update_data = {"capacity_gbps": 6000.0}
    response = client.put(f"/nodes/{fake_uuid}", json=update_data)
    assert response.status_code == 404


def test_delete_node_not_found(client):
    """Test deleting a non-existent node."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.delete(f"/nodes/{fake_uuid}")
    assert response.status_code == 404


# ==================== Enhanced Node Endpoint Tests ====================

def test_get_nodes_free_capacity_field(client, test_db):
    """Test that all nodes return free_capacity_gbps field."""
    response = client.get("/nodes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for node in data:
        assert "free_capacity_gbps" in node
        assert node["free_capacity_gbps"] >= 0
        assert node["free_capacity_gbps"] <= node["capacity_gbps"]


def test_get_nodes_with_free_capacity_filter(client, test_db):
    """Test filtering nodes by minimum free capacity."""
    response = client.get("/nodes?min_free_capacity=4000")
    assert response.status_code == 200
    data = response.json()
    # NYC-Manhattan has 5000 Gbps total, should have high free capacity
    assert len(data) >= 1
    for node in data:
        assert node["free_capacity_gbps"] >= 4000


def test_get_nodes_with_capacity_range(client, test_db):
    """Test filtering nodes by capacity range."""
    response = client.get("/nodes?min_total_capacity=2000&max_total_capacity=4000")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for node in data:
        assert 2000 <= node["capacity_gbps"] <= 4000


def test_get_nodes_geographic_filter(client, test_db):
    """Test geographic filtering around NYC."""
    # NYC coordinates: 40.7589, -73.9851
    # Should include NYC-Manhattan and nearby nodes
    response = client.get("/nodes?latitude=40.7589&longitude=-73.9851&max_distance_km=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verify NYC is in results
    nyc_found = any(node["name"] == "NYC-Manhattan" for node in data)
    assert nyc_found


def test_get_nodes_geographic_incomplete_params(client, test_db):
    """Test error when geographic parameters are incomplete."""
    # Only latitude provided
    response = client.get("/nodes?latitude=40.7589")
    assert response.status_code == 400
    assert "Geographic filtering requires all three parameters" in response.json()["detail"]

    # Only longitude provided
    response = client.get("/nodes?longitude=-73.9851")
    assert response.status_code == 400

    # Only distance provided
    response = client.get("/nodes?max_distance_km=100")
    assert response.status_code == 400


def test_get_nodes_combined_filters(client, test_db):
    """Test combining multiple filters."""
    # Vendor + free capacity
    response = client.get("/nodes?vendor=TeleConnect&min_free_capacity=1000")
    assert response.status_code == 200
    data = response.json()
    for node in data:
        assert node["vendor"] == "TeleConnect"
        assert node["free_capacity_gbps"] >= 1000


def test_get_nodes_free_capacity_with_services(client, test_db):
    """Test that free capacity decreases after creating a service."""
    # Get initial free capacity for NYC
    response = client.get(f"/nodes/{test_db['node1_uuid']}")
    initial_free = response.json()["free_capacity_gbps"]

    # Create a service from NYC to Boston
    new_service = {
        "name": "Test Service for Free Capacity",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 100.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    client.post("/services", json=new_service)

    # Check free capacity decreased
    response = client.get(f"/nodes/{test_db['node1_uuid']}")
    new_free = response.json()["free_capacity_gbps"]
    assert new_free == initial_free - 100.0


# ==================== Edge Endpoint Tests ====================

def test_get_all_edges(client, test_db):
    """Test getting all edges."""
    response = client.get("/edges")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # We created 2 edges in fixtures


def test_get_edge_by_uuid(client, test_db):
    """Test getting a specific edge by UUID."""
    edge_uuid = test_db['edge1_uuid']
    response = client.get(f"/edges/{edge_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == edge_uuid
    assert data["capacity_gbps"] == 100.0


def test_get_edge_by_uuid_not_found(client):
    """Test getting an edge with invalid UUID."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/edges/{fake_uuid}")
    assert response.status_code == 404


def test_get_edge_by_endpoints(client, test_db):
    """Test getting an edge by its endpoints."""
    node1_uuid = test_db['node1_uuid']
    node2_uuid = test_db['node2_uuid']
    response = client.get(f"/edges/by-endpoints/?node1_uuid={node1_uuid}&node2_uuid={node2_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == test_db['edge1_uuid']


def test_get_edge_by_endpoints_not_found(client, test_db):
    """Test getting a non-existent edge by endpoints."""
    node1_uuid = test_db['node1_uuid']
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/edges/by-endpoints/?node1_uuid={node1_uuid}&node2_uuid={fake_uuid}")
    assert response.status_code == 404


def test_create_edge(client, test_db):
    """Test creating a new edge."""
    new_edge = {
        "node1_uuid": test_db['node1_uuid'],
        "node2_uuid": test_db['node3_uuid'],
        "capacity_gbps": 150.0
    }
    response = client.post("/edges", json=new_edge)
    assert response.status_code == 201
    data = response.json()
    assert "uuid" in data
    assert data["capacity_gbps"] == 150.0


def test_create_edge_duplicate(client, test_db):
    """Test creating a duplicate edge."""
    duplicate_edge = {
        "node1_uuid": test_db['node1_uuid'],
        "node2_uuid": test_db['node2_uuid'],
        "capacity_gbps": 100.0
    }
    response = client.post("/edges", json=duplicate_edge)
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


def test_create_edge_invalid_node(client):
    """Test creating an edge with non-existent node."""
    fake_uuid = str(uuid_module.uuid4())
    invalid_edge = {
        "node1_uuid": fake_uuid,
        "node2_uuid": fake_uuid,
        "capacity_gbps": 100.0
    }
    response = client.post("/edges", json=invalid_edge)
    assert response.status_code == 404


def test_delete_edge_not_found(client):
    """Test deleting a non-existent edge."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.delete(f"/edges/{fake_uuid}")
    assert response.status_code == 404


# ==================== Analytics Endpoint Tests ====================

def test_get_stats(client, test_db):
    """Test getting database statistics."""
    response = client.get("/analytics/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["nodes"] == 3
    assert data["edges"] == 2
    assert "services" in data


def test_get_capacity_summary(client, test_db):
    """Test getting capacity utilization summary."""
    response = client.get("/capacity/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # We have 2 edges
    # Check that utilization_pct is 0 (no services yet)
    for edge_util in data:
        assert "uuid" in edge_util
        assert "capacity_gbps" in edge_util
        assert "utilization_pct" in edge_util


def test_get_edge_capacity(client, test_db):
    """Test getting capacity for a specific edge."""
    edge_uuid = test_db['edge1_uuid']
    response = client.get(f"/capacity/edge/{edge_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == edge_uuid
    assert data["capacity_gbps"] == 100.0
    assert data["total_demand_gbps"] == 0.0
    assert data["utilization_pct"] == 0.0


def test_get_edge_capacity_not_found(client):
    """Test getting capacity for non-existent edge."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/capacity/edge/{fake_uuid}")
    assert response.status_code == 404


def test_get_capacity_violations(client, test_db):
    """Test getting capacity violations (should be empty)."""
    response = client.get("/capacity/violations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should be empty since we haven't added any services
    assert len(data) == 0


# ==================== Service Endpoint Tests ====================

def test_get_all_services_empty(client, test_db):
    """Test getting all services when none exist."""
    response = client.get("/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_create_service(client, test_db):
    """Test creating a new service."""
    new_service = {
        "name": "Test Service NYC to Boston",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    response = client.post("/services", json=new_service)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Service NYC to Boston"
    assert "uuid" in data
    assert data["demand_gbps"] == 5.0
    assert data["hop_count"] == 1
    assert len(data["path_node_uuids"]) == 2
    assert len(data["path_edge_uuids"]) == 1


def test_create_service_auto_compute_distance(client, test_db):
    """Test creating a service with auto-computed distance."""
    new_service = {
        "name": "Test Service NYC to Boston Auto Distance",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    response = client.post("/services", json=new_service)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Service NYC to Boston Auto Distance"
    assert "uuid" in data
    assert data["demand_gbps"] == 5.0
    assert data["hop_count"] == 1
    assert len(data["path_node_uuids"]) == 2
    assert len(data["path_edge_uuids"]) == 1
    # Distance between NYC (40.7589, -73.9851) and Boston (42.3601, -71.0589)
    # Should be approximately 306 km based on haversine formula
    assert data["total_distance_km"] > 0
    assert 300 < data["total_distance_km"] < 320  # Reasonable range for NYC to Boston


def test_create_service_source_not_found(client, test_db):
    """Test creating a service with non-existent source node."""
    fake_uuid = str(uuid_module.uuid4())
    new_service = {
        "name": "Test Service",
        "source_node_uuid": fake_uuid,
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [fake_uuid, test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    response = client.post("/services", json=new_service)
    assert response.status_code == 404
    assert "Source node" in response.json()["detail"]


def test_create_service_invalid_path_node(client, test_db):
    """Test creating a service with invalid path node."""
    fake_uuid = str(uuid_module.uuid4())
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], fake_uuid, test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid'], test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    response = client.post("/services", json=new_service)
    assert response.status_code == 404
    assert "Path node" in response.json()["detail"]


def test_create_service_path_mismatch(client, test_db):
    """Test creating a service where path doesn't match endpoints."""
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node2_uuid'], test_db['node3_uuid']],  # Wrong start!
        "path_edge_uuids": [test_db['edge2_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    response = client.post("/services", json=new_service)
    assert response.status_code == 400
    assert "First node in path must match source" in response.json()["detail"]


def test_get_service_by_uuid(client, test_db):
    """Test getting a service by UUID."""
    # First create a service
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    create_response = client.post("/services", json=new_service)
    service_uuid = create_response.json()["uuid"]

    # Now get it
    response = client.get(f"/services/{service_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == service_uuid
    assert data["name"] == "Test Service"
    assert data["hop_count"] == 1


def test_get_service_not_found(client):
    """Test getting a non-existent service."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/services/{fake_uuid}")
    assert response.status_code == 404


def test_delete_service(client, test_db):
    """Test deleting a service."""
    # First create a service
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    create_response = client.post("/services", json=new_service)
    service_uuid = create_response.json()["uuid"]

    # Now delete it
    response = client.delete(f"/services/{service_uuid}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/services/{service_uuid}")
    assert get_response.status_code == 404


def test_delete_service_not_found(client):
    """Test deleting a non-existent service."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.delete(f"/services/{fake_uuid}")
    assert response.status_code == 404


def test_get_services_by_node(client, test_db):
    """Test getting services by source node."""
    # Create a service
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    client.post("/services", json=new_service)

    # Get services from node1
    response = client.get(f"/services/by-node/{test_db['node1_uuid']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(s["source_node_uuid"] == test_db['node1_uuid'] for s in data)


def test_get_services_by_node_not_found(client):
    """Test getting services for non-existent node."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/services/by-node/{fake_uuid}")
    assert response.status_code == 404


def test_get_services_by_edge(client, test_db):
    """Test getting services by edge."""
    # Create a service
    new_service = {
        "name": "Test Service",
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0,
        "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
        "path_edge_uuids": [test_db['edge1_uuid']],
        "service_timestamp": "2025-10-15T10:30:00Z"
    }
    client.post("/services", json=new_service)

    # Get services using edge1
    response = client.get(f"/services/by-edge/{test_db['edge1_uuid']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verify that edge1 is in each service's path
    for service in data:
        assert test_db['edge1_uuid'] in service["path_edge_uuids"]


def test_get_services_by_edge_not_found(client):
    """Test getting services for non-existent edge."""
    fake_uuid = str(uuid_module.uuid4())
    response = client.get(f"/services/by-edge/{fake_uuid}")
    assert response.status_code == 404


def test_get_services_with_limit(client, test_db):
    """Test getting services with limit parameter."""
    # Create multiple services
    for i in range(3):
        new_service = {
            "name": f"Test Service {i}",
            "source_node_uuid": test_db['node1_uuid'],
            "destination_node_uuid": test_db['node2_uuid'],
            "demand_gbps": 5.0,
            "path_node_uuids": [test_db['node1_uuid'], test_db['node2_uuid']],
            "path_edge_uuids": [test_db['edge1_uuid']],
            "service_timestamp": "2025-10-15T10:30:00Z"
        }
        client.post("/services", json=new_service)

    # Get with limit
    response = client.get("/services?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ==================== Routing Endpoint Tests ====================

def test_compute_route_astar_post(client, test_db):
    """Test A* routing with POST method."""
    route_request = {
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["source_node_uuid"] == test_db['node1_uuid']
    assert data["destination_node_uuid"] == test_db['node2_uuid']
    assert "path_node_uuids" in data
    assert "path_edge_uuids" in data
    assert "total_distance_km" in data
    assert "hop_count" in data
    assert "min_available_capacity" in data
    assert "computation_time_ms" in data
    assert data["demand_gbps"] == 5.0

    # Verify path makes sense
    assert len(data["path_node_uuids"]) >= 2
    assert data["path_node_uuids"][0] == test_db['node1_uuid']
    assert data["path_node_uuids"][-1] == test_db['node2_uuid']


def test_compute_route_astar_get(client, test_db):
    """Test A* routing with GET method and query params."""
    response = client.get(
        f"/routing/astar?source_node_uuid={test_db['node1_uuid']}"
        f"&destination_node_uuid={test_db['node2_uuid']}"
        f"&demand_gbps=10.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_node_uuid"] == test_db['node1_uuid']
    assert data["destination_node_uuid"] == test_db['node2_uuid']
    assert data["demand_gbps"] == 10.0


def test_compute_route_astar_source_not_found(client, test_db):
    """Test A* routing with invalid source node."""
    fake_uuid = str(uuid_module.uuid4())
    route_request = {
        "source_node_uuid": fake_uuid,
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 404
    assert "Source node" in response.json()["detail"]


def test_compute_route_astar_dest_not_found(client, test_db):
    """Test A* routing with invalid destination node."""
    fake_uuid = str(uuid_module.uuid4())
    route_request = {
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": fake_uuid,
        "demand_gbps": 5.0
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 404
    assert "Destination node" in response.json()["detail"]


def test_compute_route_astar_no_feasible_route(client, test_db):
    """Test A* routing when demand exceeds available capacity."""
    # Request unreasonably high demand that exceeds all edge capacities
    route_request = {
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 10000.0  # Much higher than our test edges
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 422
    data = response.json()
    # Response should be a detail dict with error information
    assert "detail" in data


def test_compute_route_astar_custom_demand(client, test_db):
    """Test A* routing with custom demand parameter."""
    route_request = {
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 15.0
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 200
    data = response.json()
    assert data["demand_gbps"] == 15.0
    assert data["min_available_capacity"] >= 15.0


def test_compute_route_astar_response_structure(client, test_db):
    """Test that A* route response has all required fields."""
    route_request = {
        "source_node_uuid": test_db['node1_uuid'],
        "destination_node_uuid": test_db['node2_uuid'],
        "demand_gbps": 5.0
    }
    response = client.post("/routing/astar", json=route_request)
    assert response.status_code == 200
    data = response.json()

    # Check all required fields exist
    required_fields = [
        "source_node_uuid", "destination_node_uuid", "path_node_uuids",
        "path_edge_uuids", "total_distance_km", "hop_count",
        "min_available_capacity", "computation_time_ms", "demand_gbps"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Verify types
    assert isinstance(data["path_node_uuids"], list)
    assert isinstance(data["path_edge_uuids"], list)
    assert isinstance(data["total_distance_km"], (int, float))
    assert isinstance(data["hop_count"], int)
    assert isinstance(data["min_available_capacity"], (int, float))
    assert isinstance(data["computation_time_ms"], (int, float))


# ==================== Database Method Tests ====================

def test_db_get_node_utilizations(test_db):
    """Test get_node_utilizations database method."""
    db = test_db['db']

    # Initially should be empty (no services)
    utilizations = db.get_node_utilizations()
    assert isinstance(utilizations, dict)
    assert len(utilizations) == 0

    # Create a service
    service_uuid = str(uuid_module.uuid4())
    db.insert_service_with_path(
        service_uuid=service_uuid,
        name="Test Service",
        source_node_uuid=test_db['node1_uuid'],
        destination_node_uuid=test_db['node2_uuid'],
        demand_gbps=50.0,
        hop_count=1,
        total_distance_km=350.5,
        service_timestamp="2025-10-15T10:30:00Z",
        
        path_node_uuids=[test_db['node1_uuid'], test_db['node2_uuid']],
        path_edge_uuids=[test_db['edge1_uuid']]
    )

    # Now should have utilization for node1
    utilizations = db.get_node_utilizations()
    assert test_db['node1_uuid'] in utilizations
    assert utilizations[test_db['node1_uuid']] == 50.0


def test_db_get_all_nodes_with_utilization(test_db):
    """Test get_all_nodes_with_utilization database method."""
    db = test_db['db']

    nodes = db.get_all_nodes_with_utilization()
    assert len(nodes) == 3

    # All nodes should have free_capacity_gbps field
    for node in nodes:
        assert "free_capacity_gbps" in node
        assert node["free_capacity_gbps"] >= 0
        assert node["free_capacity_gbps"] <= node["capacity_gbps"]


def test_db_node_utilization_after_service_deletion(test_db):
    """Test that node utilization updates correctly after service deletion."""
    db = test_db['db']

    # Create a service
    service_uuid = str(uuid_module.uuid4())
    db.insert_service_with_path(
        service_uuid=service_uuid,
        name="Temp Service",
        source_node_uuid=test_db['node1_uuid'],
        destination_node_uuid=test_db['node2_uuid'],
        demand_gbps=75.0,
        hop_count=1,
        total_distance_km=350.5,
        service_timestamp="2025-10-15T10:30:00Z",
        
        path_node_uuids=[test_db['node1_uuid'], test_db['node2_uuid']],
        path_edge_uuids=[test_db['edge1_uuid']]
    )

    # Check utilization
    utilizations = db.get_node_utilizations()
    assert test_db['node1_uuid'] in utilizations

    # Delete the service (need to manually update for this test)
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM services WHERE uuid = ?", (service_uuid,))
    db.conn.commit()
    cursor.close()

    # Utilization should be gone or reduced
    utilizations_after = db.get_node_utilizations()
    if test_db['node1_uuid'] in utilizations_after:
        # If other services exist, utilization should be less
        assert utilizations_after[test_db['node1_uuid']] < utilizations[test_db['node1_uuid']]
    else:
        # No utilization if no services remain
        assert test_db['node1_uuid'] not in utilizations_after
