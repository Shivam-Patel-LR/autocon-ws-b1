"""
Pydantic models for FastAPI request/response validation.
Provides schema definitions for OpenAPI/Swagger documentation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime


# ==================== Node Models ====================

class NodeBase(BaseModel):
    """Base model for node data."""
    name: str = Field(..., description="Human-readable node identifier")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    vendor: str = Field(..., description="Vendor/manufacturer name")
    capacity_gbps: float = Field(..., gt=0, description="Total capacity in Gbps")


class NodeCreate(NodeBase):
    """Model for creating a new node."""
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "Detroit-Downtown",
                "latitude": 42.3314,
                "longitude": -83.0458,
                "vendor": "TeleConnect",
                "capacity_gbps": 3500.0
            },
            {
                "name": "Chicago-Loop",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "vendor": "NetWorks",
                "capacity_gbps": 4200.0
            }
        ]
    })


class NodeUpdate(BaseModel):
    """Model for updating an existing node."""
    name: Optional[str] = Field(None, description="Human-readable node identifier")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    vendor: Optional[str] = Field(None, description="Vendor/manufacturer name")
    capacity_gbps: Optional[float] = Field(None, gt=0, description="Total capacity in Gbps")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "capacity_gbps": 6000.0,
                "vendor": "NewVendor"
            }
        ]
    })


class NodeResponse(NodeBase):
    """Model for node response with UUID."""
    uuid: str = Field(..., description="Unique node identifier")
    free_capacity_gbps: float = Field(..., ge=0, description="Available (unused) capacity in Gbps")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "examples": [
            {
                "uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "name": "NYC-Manhattan",
                "latitude": 40.7589,
                "longitude": -73.9851,
                "vendor": "TeleConnect",
                "capacity_gbps": 5000.0,
                "free_capacity_gbps": 3250.0,
                "created_at": "2025-10-15T10:30:00Z",
                "updated_at": "2025-10-15T10:30:00Z"
            }
        ]
    })


# ==================== Edge Models ====================

class EdgeBase(BaseModel):
    """Base model for edge data."""
    node1_uuid: str = Field(..., description="First node UUID")
    node2_uuid: str = Field(..., description="Second node UUID")
    capacity_gbps: float = Field(..., gt=0, description="Edge capacity in Gbps")


class EdgeCreate(EdgeBase):
    """Model for creating a new edge."""
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "node1_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "node2_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "capacity_gbps": 150.0
            }
        ]
    })


class EdgeResponse(EdgeBase):
    """Model for edge response with UUID."""
    uuid: str = Field(..., description="Unique edge identifier")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "examples": [
            {
                "uuid": "0c929850-79fc-4acd-a69d-163dc318353a",
                "node1_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "node2_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "capacity_gbps": 100.0,
                "created_at": "2025-10-15T10:30:00Z",
                "updated_at": "2025-10-15T10:30:00Z"
            }
        ]
    })


class EdgeDetailResponse(BaseModel):
    """Model for edge with human-readable node names."""
    uuid: str = Field(..., description="Unique edge identifier")
    node1_uuid: str = Field(..., description="First node UUID")
    node2_uuid: str = Field(..., description="Second node UUID")
    node1_name: str = Field(..., description="First node name")
    node2_name: str = Field(..., description="Second node name")
    capacity_gbps: float = Field(..., description="Edge capacity in Gbps")
    created_at: str = Field(..., description="Creation timestamp")


# ==================== Service Models ====================

class ServiceCreate(BaseModel):
    """Model for creating a new service with path."""
    name: str = Field(..., description="Service name")
    source_node_uuid: str = Field(..., description="Source node UUID")
    destination_node_uuid: str = Field(..., description="Destination node UUID")
    demand_gbps: float = Field(..., gt=0, description="Bandwidth demand in Gbps")
    path_node_uuids: List[str] = Field(..., min_length=2, description="Ordered list of node UUIDs in path")
    path_edge_uuids: List[str] = Field(..., min_length=1, description="Ordered list of edge UUIDs in path")
    service_timestamp: str = Field(..., description="Service timestamp (ISO 8601)")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "NYC to Boston Service",
                "source_node_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "destination_node_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "demand_gbps": 10.0,
                "path_node_uuids": [
                    "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                    "7e518bf4-bf70-4e95-a164-0697b07795b1"
                ],
                "path_edge_uuids": [
                    "0c929850-79fc-4acd-a69d-163dc318353a"
                ],
                "service_timestamp": "2025-10-15T10:30:00Z"
            },
            {
                "name": "Multi-hop Service",
                "source_node_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "destination_node_uuid": "abc123-4567-89de-f012-345678901234",
                "demand_gbps": 5.0,
                "path_node_uuids": [
                    "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                    "7e518bf4-bf70-4e95-a164-0697b07795b1",
                    "abc123-4567-89de-f012-345678901234"
                ],
                "path_edge_uuids": [
                    "0c929850-79fc-4acd-a69d-163dc318353a",
                    "def456-7890-12ab-cdef-567890123456"
                ],
                "service_timestamp": "2025-10-15T14:20:00Z"
            }
        ]
    })

    @field_validator('path_node_uuids')
    @classmethod
    def validate_path_nodes(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("Path must have at least 2 nodes")
        return v

    @field_validator('path_edge_uuids')
    @classmethod
    def validate_path_edges(cls, v: List[str], info) -> List[str]:
        # Edge count should be node count - 1
        if 'path_node_uuids' in info.data:
            expected_edges = len(info.data['path_node_uuids']) - 1
            if len(v) != expected_edges:
                raise ValueError(f"Expected {expected_edges} edges for path, got {len(v)}")
        return v


class ServiceResponse(BaseModel):
    """Model for service response with UUID and path."""
    uuid: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Service name")
    source_node_uuid: str = Field(..., description="Source node UUID")
    destination_node_uuid: str = Field(..., description="Destination node UUID")
    demand_gbps: float = Field(..., gt=0, description="Bandwidth demand in Gbps")
    hop_count: int = Field(..., ge=1, description="Number of hops")
    total_distance_km: float = Field(..., ge=0, description="Total path distance in km")
    service_timestamp: str = Field(..., description="Service timestamp")
    path_node_uuids: List[str] = Field(..., description="Ordered list of node UUIDs in path")
    path_edge_uuids: List[str] = Field(..., description="Ordered list of edge UUIDs in path")
    created_at: str = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ServiceDetailResponse(ServiceResponse):
    """Model for service with human-readable node names."""
    source_name: str = Field(..., description="Source node name")
    destination_name: str = Field(..., description="Destination node name")


# ==================== Capacity Models ====================

class EdgeUtilizationResponse(BaseModel):
    """Model for edge capacity utilization."""
    uuid: str = Field(..., description="Edge UUID")
    capacity_gbps: float = Field(..., description="Total edge capacity")
    total_demand_gbps: float = Field(..., description="Total allocated demand")
    service_count: int = Field(..., description="Number of services using this edge")
    utilization_pct: float = Field(..., description="Utilization percentage")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "uuid": "0c929850-79fc-4acd-a69d-163dc318353a",
                "capacity_gbps": 100.0,
                "total_demand_gbps": 45.0,
                "service_count": 9,
                "utilization_pct": 45.0
            }
        ]
    })


class CapacityViolationResponse(BaseModel):
    """Model for capacity constraint violation."""
    edge_uuid: str = Field(..., description="Edge UUID")
    capacity_gbps: float = Field(..., description="Total edge capacity")
    total_demand_gbps: float = Field(..., description="Total allocated demand")
    overage: float = Field(..., description="Capacity overage (demand - capacity)")


# ==================== Analytics Models ====================

class DatabaseStatsResponse(BaseModel):
    """Model for database statistics."""
    nodes: int = Field(..., description="Total number of nodes")
    edges: int = Field(..., description="Total number of edges")
    services: int = Field(..., description="Total number of services")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "nodes": 48,
                "edges": 200,
                "services": 100
            }
        ]
    })


class NodeStatsResponse(BaseModel):
    """Model for node statistics."""
    name: str = Field(..., description="Node name")
    service_count: int = Field(..., description="Number of services using this node as endpoint")
    capacity_gbps: float = Field(..., description="Node capacity")


class HopDistributionResponse(BaseModel):
    """Model for hop count distribution."""
    hop_count: int = Field(..., description="Number of hops")
    service_count: int = Field(..., description="Number of services with this hop count")


# ==================== Health & Info Models ====================

class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str = Field(..., description="Health status")
    database: str = Field(..., description="Database status")
    timestamp: str = Field(..., description="Current timestamp")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2025-10-15T15:41:56.883504Z"
            }
        ]
    })


class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str = Field(..., description="Error message")


# ==================== Routing Models ====================

class RouteRequest(BaseModel):
    """Model for requesting a route between two nodes."""
    source_node_uuid: str = Field(..., description="Source node UUID")
    destination_node_uuid: str = Field(..., description="Destination node UUID")
    demand_gbps: float = Field(5.0, gt=0, description="Required bandwidth in Gbps (default: 5.0)")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "source_node_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "destination_node_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "demand_gbps": 10.0
            }
        ]
    })


class RouteResponse(BaseModel):
    """Model for route computation response."""
    source_node_uuid: str = Field(..., description="Source node UUID")
    destination_node_uuid: str = Field(..., description="Destination node UUID")
    path_node_uuids: List[str] = Field(..., description="Ordered list of node UUIDs in path")
    path_edge_uuids: List[str] = Field(..., description="Ordered list of edge UUIDs in path")
    total_distance_km: float = Field(..., description="Total geographic distance in km")
    hop_count: int = Field(..., description="Number of hops in path")
    min_available_capacity: float = Field(..., description="Bottleneck capacity along path (Gbps)")
    computation_time_ms: float = Field(..., description="Time taken to compute route (ms)")
    demand_gbps: float = Field(..., description="Requested bandwidth (Gbps)")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "source_node_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "destination_node_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "path_node_uuids": ["f9581593-4f1f-4da5-83ba-73aacd2cc101", "abc123", "7e518bf4-bf70-4e95-a164-0697b07795b1"],
                "path_edge_uuids": ["edge-uuid-1", "edge-uuid-2"],
                "total_distance_km": 234.56,
                "hop_count": 2,
                "min_available_capacity": 45.5,
                "computation_time_ms": 12.34,
                "demand_gbps": 10.0
            }
        ]
    })


class RouteNotFoundResponse(BaseModel):
    """Model for route not found error."""
    source_node_uuid: str = Field(..., description="Source node UUID")
    destination_node_uuid: str = Field(..., description="Destination node UUID")
    demand_gbps: float = Field(..., description="Requested bandwidth (Gbps)")
    error: str = Field(..., description="Error message")
    reason: str = Field(..., description="Reason why no route was found")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "source_node_uuid": "f9581593-4f1f-4da5-83ba-73aacd2cc101",
                "destination_node_uuid": "7e518bf4-bf70-4e95-a164-0697b07795b1",
                "demand_gbps": 500.0,
                "error": "No feasible route found",
                "reason": "No path exists with sufficient capacity for demand of 500.0 Gbps"
            }
        ]
    })
