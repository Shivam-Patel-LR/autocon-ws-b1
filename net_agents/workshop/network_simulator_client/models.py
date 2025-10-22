"""
Pydantic models for Network Simulator API requests and responses.

This module defines all data models used for API communication,
including request payloads and response schemas with full validation.
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ==================== Health & Status Models ====================

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(description="Health status of the API")
    database: str = Field(description="Database connectivity status")
    timestamp: Optional[str] = Field(None, description="Timestamp of health check")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2024-01-15T12:00:00Z"
            }
        }


# ==================== Node Models ====================

class NodeCreate(BaseModel):
    """Request model for creating a new network node."""
    name: str = Field(description="Unique name for the node")
    latitude: float = Field(ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(ge=-180, le=180, description="Longitude coordinate (-180 to 180)")
    vendor: str = Field(description="Network equipment vendor")
    capacity_gbps: float = Field(gt=0, description="Total capacity in Gbps (must be > 0)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "NYC-Core-01",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "vendor": "Cisco",
                "capacity_gbps": 100.0
            }
        }


class NodeUpdate(BaseModel):
    """Request model for updating an existing node."""
    name: Optional[str] = Field(None, description="Updated node name")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Updated latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Updated longitude")
    vendor: Optional[str] = Field(None, description="Updated vendor")
    capacity_gbps: Optional[float] = Field(None, gt=0, description="Updated capacity in Gbps")

    class Config:
        json_schema_extra = {
            "example": {
                "capacity_gbps": 200.0,
                "vendor": "Juniper"
            }
        }


class NodeResponse(BaseModel):
    """Response model for node data."""
    uuid: str = Field(description="Unique identifier for the node")
    name: str = Field(description="Node name")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    vendor: str = Field(description="Network equipment vendor")
    capacity_gbps: float = Field(description="Total capacity in Gbps")
    free_capacity_gbps: float = Field(description="Available capacity in Gbps")
    created_at: str = Field(description="ISO 8601 timestamp of creation")
    updated_at: str = Field(description="ISO 8601 timestamp of last update")

    @field_validator('free_capacity_gbps')
    @classmethod
    def validate_free_capacity(cls, v: float, info) -> float:
        """Ensure free capacity is non-negative."""
        if v < 0:
            raise ValueError("Free capacity cannot be negative")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "name": "NYC-Core-01",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "vendor": "Cisco",
                "capacity_gbps": 100.0,
                "free_capacity_gbps": 75.5,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


# ==================== Edge Models ====================

class EdgeCreate(BaseModel):
    """Request model for creating a new network edge (connection)."""
    node1_uuid: str = Field(description="UUID of the first node")
    node2_uuid: str = Field(description="UUID of the second node")
    capacity_gbps: float = Field(gt=0, description="Edge capacity in Gbps (must be > 0)")

    @model_validator(mode='after')
    def validate_different_nodes(self):
        """Ensure edge connects two different nodes."""
        if self.node1_uuid == self.node2_uuid:
            raise ValueError("Edge must connect two different nodes")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "node1_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "node2_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "capacity_gbps": 50.0
            }
        }


class EdgeResponse(BaseModel):
    """Response model for edge data."""
    uuid: str = Field(description="Unique identifier for the edge")
    node1_uuid: str = Field(description="UUID of the first node")
    node2_uuid: str = Field(description="UUID of the second node")
    capacity_gbps: float = Field(description="Edge capacity in Gbps")
    created_at: str = Field(description="ISO 8601 timestamp of creation")
    updated_at: str = Field(description="ISO 8601 timestamp of last update")

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "node1_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "node2_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "capacity_gbps": 50.0,
                "created_at": "2024-01-15T10:35:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }


# ==================== Service Models ====================

class ServiceCreate(BaseModel):
    """Request model for creating a new service."""
    name: str = Field(description="Service name")
    source_node_uuid: str = Field(description="UUID of the source node")
    destination_node_uuid: str = Field(description="UUID of the destination node")
    demand_gbps: float = Field(gt=0, description="Bandwidth demand in Gbps (must be > 0)")
    path_node_uuids: List[str] = Field(min_length=2, description="Ordered list of node UUIDs in the path (minimum 2)")
    path_edge_uuids: List[str] = Field(min_length=1, description="Ordered list of edge UUIDs in the path (minimum 1)")
    service_timestamp: str = Field(description="ISO 8601 timestamp for the service")

    @model_validator(mode='after')
    def validate_service_path(self):
        """Validate service path consistency."""
        # Check source and destination
        if self.source_node_uuid == self.destination_node_uuid:
            raise ValueError("Source and destination must be different")

        # Check path starts at source
        if self.path_node_uuids[0] != self.source_node_uuid:
            raise ValueError("Path must start at source node")

        # Check path ends at destination
        if self.path_node_uuids[-1] != self.destination_node_uuid:
            raise ValueError("Path must end at destination node")

        # Check edge count matches node count
        expected_edges = len(self.path_node_uuids) - 1
        if len(self.path_edge_uuids) != expected_edges:
            raise ValueError(
                f"Edge count ({len(self.path_edge_uuids)}) must equal node count - 1 ({expected_edges})"
            )

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Service-NYC-BOS-001",
                "source_node_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "destination_node_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "demand_gbps": 10.0,
                "path_node_uuids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                ],
                "path_edge_uuids": [
                    "edge-uuid-1",
                    "edge-uuid-2"
                ],
                "service_timestamp": "2024-01-15T12:00:00Z"
            }
        }


class ServiceResponse(BaseModel):
    """Response model for service data."""
    uuid: str = Field(description="Unique identifier for the service")
    name: str = Field(description="Service name")
    source_node_uuid: str = Field(description="UUID of the source node")
    destination_node_uuid: str = Field(description="UUID of the destination node")
    demand_gbps: float = Field(description="Bandwidth demand in Gbps")
    hop_count: int = Field(ge=1, description="Number of hops in the path")
    total_distance_km: float = Field(description="Total path distance in kilometers")
    service_timestamp: str = Field(description="ISO 8601 timestamp for the service")
    path_node_uuids: List[str] = Field(description="Ordered list of node UUIDs in the path")
    path_edge_uuids: List[str] = Field(description="Ordered list of edge UUIDs in the path")
    created_at: str = Field(description="ISO 8601 timestamp of creation")

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "service-uuid-123",
                "name": "Service-NYC-BOS-001",
                "source_node_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "destination_node_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "demand_gbps": 10.0,
                "hop_count": 2,
                "total_distance_km": 347.5,
                "service_timestamp": "2024-01-15T12:00:00Z",
                "path_node_uuids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                ],
                "path_edge_uuids": [
                    "edge-uuid-1",
                    "edge-uuid-2"
                ],
                "created_at": "2024-01-15T12:05:00Z"
            }
        }


# ==================== Routing Models ====================

class RouteRequest(BaseModel):
    """Request model for computing a route between nodes."""
    source_node_uuid: str = Field(description="UUID of the source node")
    destination_node_uuid: str = Field(description="UUID of the destination node")
    demand_gbps: float = Field(default=5.0, gt=0, description="Bandwidth demand in Gbps (default: 5.0)")

    @model_validator(mode='after')
    def validate_different_nodes(self):
        """Ensure source and destination are different."""
        if self.source_node_uuid == self.destination_node_uuid:
            raise ValueError("Source and destination must be different")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "source_node_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "destination_node_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "demand_gbps": 10.0
            }
        }


class RouteResponse(BaseModel):
    """Response model for computed route."""
    source_node_uuid: str = Field(description="UUID of the source node")
    destination_node_uuid: str = Field(description="UUID of the destination node")
    path_node_uuids: List[str] = Field(description="Ordered list of node UUIDs in the route")
    path_edge_uuids: List[str] = Field(description="Ordered list of edge UUIDs in the route")
    total_distance_km: float = Field(description="Total route distance in kilometers")
    hop_count: int = Field(description="Number of hops in the route")
    min_available_capacity: float = Field(description="Bottleneck capacity along the route in Gbps")
    computation_time_ms: float = Field(description="Time taken to compute the route in milliseconds")
    demand_gbps: float = Field(description="Requested bandwidth demand in Gbps")

    class Config:
        json_schema_extra = {
            "example": {
                "source_node_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "destination_node_uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "path_node_uuids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                ],
                "path_edge_uuids": [
                    "edge-uuid-1",
                    "edge-uuid-2"
                ],
                "total_distance_km": 347.5,
                "hop_count": 2,
                "min_available_capacity": 45.0,
                "computation_time_ms": 2.5,
                "demand_gbps": 10.0
            }
        }


# ==================== Analytics & Capacity Models ====================

class DatabaseStatsResponse(BaseModel):
    """Response model for database statistics."""
    nodes: int = Field(description="Total number of nodes")
    edges: int = Field(description="Total number of edges")
    services: int = Field(description="Total number of services")

    class Config:
        json_schema_extra = {
            "example": {
                "nodes": 48,
                "edges": 196,
                "services": 150
            }
        }


class EdgeUtilizationResponse(BaseModel):
    """Response model for edge capacity utilization."""
    uuid: str = Field(description="Edge UUID")
    capacity_gbps: float = Field(description="Total edge capacity in Gbps")
    total_demand_gbps: float = Field(description="Total demand on the edge in Gbps")
    service_count: int = Field(description="Number of services using this edge")
    utilization_pct: float = Field(description="Utilization percentage (0-100+)")

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "capacity_gbps": 50.0,
                "total_demand_gbps": 35.5,
                "service_count": 4,
                "utilization_pct": 71.0
            }
        }


class CapacityViolationResponse(BaseModel):
    """Response model for capacity violations."""
    edge_uuid: str = Field(description="UUID of the edge with capacity violation")
    capacity_gbps: float = Field(description="Edge capacity in Gbps")
    total_demand_gbps: float = Field(description="Total demand exceeding capacity in Gbps")
    overage: float = Field(description="Amount by which demand exceeds capacity in Gbps")

    class Config:
        json_schema_extra = {
            "example": {
                "edge_uuid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "capacity_gbps": 50.0,
                "total_demand_gbps": 65.0,
                "overage": 15.0
            }
        }
