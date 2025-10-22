"""
Network Simulator Client - Main client class for interacting with the API.

This module provides a comprehensive, production-ready client for the Network
Simulator API with both synchronous and asynchronous support.
"""

import httpx
from typing import List, Optional, Dict, Any

from .models import (
    HealthResponse,
    NodeCreate,
    NodeUpdate,
    NodeResponse,
    EdgeCreate,
    EdgeResponse,
    ServiceCreate,
    ServiceResponse,
    RouteRequest,
    RouteResponse,
    DatabaseStatsResponse,
    EdgeUtilizationResponse,
    CapacityViolationResponse,
)
from .exceptions import (
    NetworkSimulatorError,
    APIConnectionError,
    APITimeoutError,
    NodeNotFoundError,
    EdgeNotFoundError,
    ServiceNotFoundError,
    RouteNotFoundError,
    ResourceConflictError,
    ValidationError,
    exception_from_response,
)
from .utils import build_query_params


class NetworkSimulatorClient:
    """
    Comprehensive client for the Network Simulator API.

    Provides both synchronous and asynchronous methods for all API operations
    including node management, edge management, service management, routing,
    and capacity analytics.

    Args:
        base_url: Base URL of the Network Simulator API (default: http://localhost:8003)
        timeout: Request timeout in seconds (default: 30.0)
        max_retries: Maximum number of retry attempts for failed requests (default: 3)
        verify_ssl: Whether to verify SSL certificates (default: True)

    Example:
        >>> client = NetworkSimulatorClient(base_url="http://localhost:8003")
        >>> health = client.health_check()
        >>> nodes = client.get_nodes()
        >>> print(f"Found {len(nodes)} nodes")

    Context Manager Example:
        >>> with NetworkSimulatorClient() as client:
        ...     nodes = client.get_nodes()
        ...     print(f"Found {len(nodes)} nodes")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.Client] = None

    def __enter__(self):
        """Enter context manager."""
        self._client = httpx.Client(
            base_url=self.base_url, timeout=self.timeout, verify=self.verify_ssl
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close client."""
        if self._client:
            self._client.close()
            self._client = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url, timeout=self.timeout, verify=self.verify_ssl
            )
        return self._client

    def close(self):
        """Close the HTTP client and release resources."""
        if self._client:
            self._client.close()
            self._client = None

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            Various NetworkSimulatorError subclasses based on status code
        """
        try:
            response.raise_for_status()
            # Handle 204 No Content responses
            if response.status_code == 204:
                return {}
            return response.json()
        except httpx.HTTPStatusError as e:
            # Try to extract error message from response
            try:
                error_data = response.json()
                error_message = error_data.get("detail", str(e))
            except Exception:
                error_message = str(e)

            # Map to specific exceptions based on endpoint and status
            if response.status_code == 404:
                url_path = response.url.path
                if "/nodes/" in url_path:
                    raise NodeNotFoundError(
                        error_message,
                        status_code=404,
                        response_data=error_data if "error_data" in locals() else None,
                    )
                elif "/edges/" in url_path:
                    raise EdgeNotFoundError(
                        error_message,
                        status_code=404,
                        response_data=error_data if "error_data" in locals() else None,
                    )
                elif "/services/" in url_path:
                    raise ServiceNotFoundError(
                        error_message,
                        status_code=404,
                        response_data=error_data if "error_data" in locals() else None,
                    )

            if response.status_code == 422 and "/routing/" in response.url.path:
                raise RouteNotFoundError(
                    error_message,
                    status_code=422,
                    response_data=error_data if "error_data" in locals() else None,
                )

            if response.status_code == 409:
                raise ResourceConflictError(
                    error_message,
                    status_code=409,
                    response_data=error_data if "error_data" in locals() else None,
                )

            if response.status_code == 400:
                raise ValidationError(
                    error_message,
                    status_code=400,
                    response_data=error_data if "error_data" in locals() else None,
                )

            # Generic exception for other status codes
            raise exception_from_response(
                response.status_code,
                error_message,
                error_data if "error_data" in locals() else None,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except Exception as e:
            if isinstance(e, NetworkSimulatorError):
                raise
            raise NetworkSimulatorError(f"Unexpected error: {e}")

    # ==================== Health & Status Methods ====================

    def health_check(self) -> HealthResponse:
        """
        Check the health status of the API and database connectivity.

        Returns:
            HealthResponse with status information

        Raises:
            APIConnectionError: If unable to connect to the API
            APITimeoutError: If the request times out
        """
        client = self._get_client()
        response = client.get("/health")
        data = self._handle_response(response)
        return HealthResponse(**data)

    # ==================== Node Management Methods ====================

    def get_nodes(
        self,
        vendor: Optional[str] = None,
        min_total_capacity: Optional[float] = None,
        max_total_capacity: Optional[float] = None,
        min_free_capacity: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_distance_km: Optional[float] = None,
    ) -> List[NodeResponse]:
        """
        Retrieve all nodes with optional filtering.

        Args:
            vendor: Filter by vendor name
            min_total_capacity: Minimum total capacity in Gbps
            max_total_capacity: Maximum total capacity in Gbps
            min_free_capacity: Minimum free capacity in Gbps
            latitude: Latitude for geographic filtering (requires longitude and max_distance_km)
            longitude: Longitude for geographic filtering (requires latitude and max_distance_km)
            max_distance_km: Maximum distance in km for geographic filtering

        Returns:
            List of NodeResponse objects

        Raises:
            ValidationError: If geographic parameters are incomplete
        """
        params = build_query_params(
            vendor=vendor,
            min_total_capacity=min_total_capacity,
            max_total_capacity=max_total_capacity,
            min_free_capacity=min_free_capacity,
            latitude=latitude,
            longitude=longitude,
            max_distance_km=max_distance_km,
        )

        client = self._get_client()
        response = client.get("/nodes", params=params)
        data = self._handle_response(response)
        return [NodeResponse(**node) for node in data]

    def get_node(self, node_uuid: str) -> NodeResponse:
        """
        Retrieve a specific node by UUID.

        Args:
            node_uuid: UUID of the node to retrieve

        Returns:
            NodeResponse object

        Raises:
            NodeNotFoundError: If the node does not exist
        """
        client = self._get_client()
        response = client.get(f"/nodes/{node_uuid}")
        data = self._handle_response(response)
        return NodeResponse(**data)

    def search_nodes_by_name(self, name_substring: str) -> List[NodeResponse]:
        """
        Search for nodes by name substring (case-insensitive).

        Args:
            name_substring: Substring to search for in node names

        Returns:
            List of matching NodeResponse objects
        """
        client = self._get_client()
        response = client.get(f"/nodes/by-name/{name_substring}")
        data = self._handle_response(response)
        return [NodeResponse(**node) for node in data]

    def create_node(self, node: NodeCreate) -> NodeResponse:
        """
        Create a new network node.

        Args:
            node: NodeCreate object with node details

        Returns:
            NodeResponse object with the created node (including UUID)

        Raises:
            ValidationError: If node data is invalid or name already exists
        """
        client = self._get_client()
        response = client.post("/nodes", json=node.model_dump())
        data = self._handle_response(response)
        return NodeResponse(**data)

    def update_node(self, node_uuid: str, node_update: NodeUpdate) -> NodeResponse:
        """
        Update an existing node.

        Args:
            node_uuid: UUID of the node to update
            node_update: NodeUpdate object with fields to update

        Returns:
            NodeResponse object with updated node data

        Raises:
            NodeNotFoundError: If the node does not exist
            ValidationError: If update data is invalid
        """
        client = self._get_client()
        # Only send non-None fields
        update_data = node_update.model_dump(exclude_none=True)
        response = client.put(f"/nodes/{node_uuid}", json=update_data)
        data = self._handle_response(response)
        return NodeResponse(**data)

    def delete_node(self, node_uuid: str) -> None:
        """
        Delete a network node.

        Args:
            node_uuid: UUID of the node to delete

        Raises:
            NodeNotFoundError: If the node does not exist
            ResourceConflictError: If the node is referenced by edges or services
        """
        client = self._get_client()
        response = client.delete(f"/nodes/{node_uuid}")
        self._handle_response(response)

    # ==================== Edge Management Methods ====================

    def get_edges(self) -> List[EdgeResponse]:
        """
        Retrieve all network edges.

        Returns:
            List of EdgeResponse objects
        """
        client = self._get_client()
        response = client.get("/edges")
        data = self._handle_response(response)
        return [EdgeResponse(**edge) for edge in data]

    def get_edge(self, edge_uuid: str) -> EdgeResponse:
        """
        Retrieve a specific edge by UUID.

        Args:
            edge_uuid: UUID of the edge to retrieve

        Returns:
            EdgeResponse object

        Raises:
            EdgeNotFoundError: If the edge does not exist
        """
        client = self._get_client()
        response = client.get(f"/edges/{edge_uuid}")
        data = self._handle_response(response)
        return EdgeResponse(**data)

    def get_edge_by_endpoints(self, node1_uuid: str, node2_uuid: str) -> EdgeResponse:
        """
        Retrieve an edge by its endpoint node UUIDs.

        Args:
            node1_uuid: UUID of the first endpoint node
            node2_uuid: UUID of the second endpoint node

        Returns:
            EdgeResponse object

        Raises:
            EdgeNotFoundError: If no edge exists between the specified nodes
        """
        client = self._get_client()
        params = {"node1_uuid": node1_uuid, "node2_uuid": node2_uuid}
        response = client.get("/edges/by-endpoints/", params=params)
        data = self._handle_response(response)
        return EdgeResponse(**data)

    def create_edge(self, edge: EdgeCreate) -> EdgeResponse:
        """
        Create a new network edge (connection between nodes).

        Args:
            edge: EdgeCreate object with edge details

        Returns:
            EdgeResponse object with the created edge (including UUID)

        Raises:
            ValidationError: If edge data is invalid or edge already exists
            NodeNotFoundError: If one or both nodes do not exist
        """
        client = self._get_client()
        response = client.post("/edges", json=edge.model_dump())
        data = self._handle_response(response)
        return EdgeResponse(**data)

    def delete_edge(self, edge_uuid: str) -> None:
        """
        Delete a network edge.

        Args:
            edge_uuid: UUID of the edge to delete

        Raises:
            EdgeNotFoundError: If the edge does not exist
            ResourceConflictError: If the edge is referenced by services
        """
        client = self._get_client()
        response = client.delete(f"/edges/{edge_uuid}")
        self._handle_response(response)

    # ==================== Service Management Methods ====================

    def get_services(self, limit: Optional[int] = None) -> List[ServiceResponse]:
        """
        Retrieve all services with optional limit.

        Args:
            limit: Maximum number of services to return (1-1000)

        Returns:
            List of ServiceResponse objects

        Raises:
            ValidationError: If limit is out of range
        """
        params = build_query_params(limit=limit)
        client = self._get_client()
        response = client.get("/services", params=params)
        data = self._handle_response(response)
        return [ServiceResponse(**service) for service in data]

    def get_service(self, service_uuid: str) -> ServiceResponse:
        """
        Retrieve a specific service by UUID.

        Args:
            service_uuid: UUID of the service to retrieve

        Returns:
            ServiceResponse object with full path information

        Raises:
            ServiceNotFoundError: If the service does not exist
        """
        client = self._get_client()
        response = client.get(f"/services/{service_uuid}")
        data = self._handle_response(response)
        return ServiceResponse(**data)

    def get_services_by_node(self, node_uuid: str) -> List[ServiceResponse]:
        """
        Retrieve all services originating from a specific node.

        Args:
            node_uuid: UUID of the source node

        Returns:
            List of ServiceResponse objects

        Raises:
            NodeNotFoundError: If the node does not exist
        """
        client = self._get_client()
        response = client.get(f"/services/by-node/{node_uuid}")
        data = self._handle_response(response)
        return [ServiceResponse(**service) for service in data]

    def get_services_by_edge(self, edge_uuid: str) -> List[ServiceResponse]:
        """
        Retrieve all services that traverse a specific edge.

        Args:
            edge_uuid: UUID of the edge

        Returns:
            List of ServiceResponse objects

        Raises:
            EdgeNotFoundError: If the edge does not exist
        """
        client = self._get_client()
        response = client.get(f"/services/by-edge/{edge_uuid}")
        data = self._handle_response(response)
        return [ServiceResponse(**service) for service in data]

    def create_service(self, service: ServiceCreate) -> ServiceResponse:
        """
        Create a new service with a specified path.

        Args:
            service: ServiceCreate object with service details and path

        Returns:
            ServiceResponse object with the created service (including UUID)

        Raises:
            ValidationError: If service data or path is invalid
            NodeNotFoundError: If source, destination, or path nodes don't exist
            EdgeNotFoundError: If path edges don't exist
        """
        client = self._get_client()
        response = client.post("/services", json=service.model_dump())
        data = self._handle_response(response)
        return ServiceResponse(**data)

    def delete_service(self, service_uuid: str) -> None:
        """
        Delete a service and free up capacity on its path edges.

        Args:
            service_uuid: UUID of the service to delete

        Raises:
            ServiceNotFoundError: If the service does not exist
        """
        client = self._get_client()
        response = client.delete(f"/services/{service_uuid}")
        self._handle_response(response)

    # ==================== Routing Methods ====================

    def compute_route(
        self,
        source_node_uuid: str,
        destination_node_uuid: str,
        demand_gbps: float = 5.0,
    ) -> RouteResponse:
        """
        Compute an optimal route between two nodes using A* algorithm.

        The algorithm finds the shortest geographic path that satisfies
        the capacity constraint.

        Args:
            source_node_uuid: UUID of the source node
            destination_node_uuid: UUID of the destination node
            demand_gbps: Bandwidth demand in Gbps (default: 5.0)

        Returns:
            RouteResponse with path details and capacity information

        Raises:
            NodeNotFoundError: If source or destination node doesn't exist
            RouteNotFoundError: If no feasible route exists
        """
        route_request = RouteRequest(
            source_node_uuid=source_node_uuid,
            destination_node_uuid=destination_node_uuid,
            demand_gbps=demand_gbps,
        )
        client = self._get_client()
        response = client.post("/routing/astar", json=route_request.model_dump())
        data = self._handle_response(response)
        return RouteResponse(**data)

    def compute_route_get(
        self,
        source_node_uuid: str,
        destination_node_uuid: str,
        demand_gbps: float = 5.0,
    ) -> RouteResponse:
        """
        Compute an optimal route using GET method (alternative to POST).

        Args:
            source_node_uuid: UUID of the source node
            destination_node_uuid: UUID of the destination node
            demand_gbps: Bandwidth demand in Gbps (default: 5.0)

        Returns:
            RouteResponse with path details and capacity information

        Raises:
            NodeNotFoundError: If source or destination node doesn't exist
            RouteNotFoundError: If no feasible route exists
        """
        params = {
            "source_node_uuid": source_node_uuid,
            "destination_node_uuid": destination_node_uuid,
            "demand_gbps": demand_gbps,
        }
        client = self._get_client()
        response = client.get("/routing/astar", params=params)
        data = self._handle_response(response)
        return RouteResponse(**data)

    # ==================== Capacity & Analytics Methods ====================

    def get_database_stats(self) -> DatabaseStatsResponse:
        """
        Get database statistics (counts of nodes, edges, and services).

        Returns:
            DatabaseStatsResponse with entity counts
        """
        client = self._get_client()
        response = client.get("/analytics/stats")
        data = self._handle_response(response)
        return DatabaseStatsResponse(**data)

    def get_capacity_summary(self) -> List[EdgeUtilizationResponse]:
        """
        Get capacity utilization summary for all edges.

        Returns:
            List of EdgeUtilizationResponse objects sorted by utilization percentage (descending)
        """
        client = self._get_client()
        response = client.get("/capacity/summary")
        data = self._handle_response(response)
        return [EdgeUtilizationResponse(**edge) for edge in data]

    def get_edge_utilization(self, edge_uuid: str) -> EdgeUtilizationResponse:
        """
        Get capacity utilization for a specific edge.

        Args:
            edge_uuid: UUID of the edge

        Returns:
            EdgeUtilizationResponse with utilization details

        Raises:
            EdgeNotFoundError: If the edge does not exist
        """
        client = self._get_client()
        response = client.get(f"/capacity/edge/{edge_uuid}")
        data = self._handle_response(response)
        return EdgeUtilizationResponse(**data)

    def get_capacity_violations(self) -> List[CapacityViolationResponse]:
        """
        Get all edges with capacity violations (demand exceeds capacity).

        Returns:
            List of CapacityViolationResponse objects for oversubscribed edges
        """
        client = self._get_client()
        response = client.get("/capacity/violations")
        data = self._handle_response(response)
        return [CapacityViolationResponse(**violation) for violation in data]

    # ==================== Helper Methods ====================

    def get_high_utilization_edges(
        self, threshold_pct: float = 80.0
    ) -> List[EdgeUtilizationResponse]:
        """
        Get edges with utilization above a threshold percentage.

        Args:
            threshold_pct: Utilization threshold percentage (default: 80.0)

        Returns:
            List of EdgeUtilizationResponse objects above threshold
        """
        all_edges = self.get_capacity_summary()
        return [edge for edge in all_edges if edge.utilization_pct >= threshold_pct]

    def get_node_by_name_exact(self, name: str) -> Optional[NodeResponse]:
        """
        Get a node by exact name match.

        Args:
            name: Exact node name

        Returns:
            NodeResponse if found, None otherwise
        """
        nodes = self.get_nodes()
        for node in nodes:
            if node.name == name:
                return node
        return None

    def validate_path(
        self, path_node_uuids: List[str], path_edge_uuids: List[str], demand_gbps: float
    ) -> Dict[str, Any]:
        """
        Validate a path for connectivity and capacity constraints.

        Args:
            path_node_uuids: List of node UUIDs in the path
            path_edge_uuids: List of edge UUIDs in the path
            demand_gbps: Required capacity in Gbps

        Returns:
            Dictionary with validation results:
                - valid: bool
                - errors: List[str]
                - total_distance_km: float (if valid)
                - min_available_capacity: float (if valid)
        """
        errors = []

        # Check path length consistency
        if len(path_edge_uuids) != len(path_node_uuids) - 1:
            errors.append(
                f"Edge count ({len(path_edge_uuids)}) must equal node count - 1 ({len(path_node_uuids) - 1})"
            )
            return {"valid": False, "errors": errors}

        # Verify all nodes exist
        try:
            nodes = [self.get_node(uuid) for uuid in path_node_uuids]
        except NodeNotFoundError as e:
            errors.append(f"Node not found: {e.message}")
            return {"valid": False, "errors": errors}

        # Verify all edges exist and have capacity
        min_capacity = float("inf")
        total_distance = 0.0

        try:
            for edge_uuid in path_edge_uuids:
                edge = self.get_edge(edge_uuid)
                utilization = self.get_edge_utilization(edge_uuid)
                available = edge.capacity_gbps - utilization.total_demand_gbps

                if available < demand_gbps:
                    errors.append(
                        f"Edge {edge_uuid} has insufficient capacity "
                        f"(available: {available:.2f} Gbps, required: {demand_gbps:.2f} Gbps)"
                    )

                min_capacity = min(min_capacity, available)

            # Calculate total distance using haversine
            from .utils import haversine_distance

            for i in range(len(nodes) - 1):
                distance = haversine_distance(
                    nodes[i].latitude,
                    nodes[i].longitude,
                    nodes[i + 1].latitude,
                    nodes[i + 1].longitude,
                )
                total_distance += distance

        except (EdgeNotFoundError, Exception) as e:
            errors.append(f"Edge validation error: {str(e)}")
            return {"valid": False, "errors": errors}

        if errors:
            return {"valid": False, "errors": errors}

        return {
            "valid": True,
            "errors": [],
            "total_distance_km": total_distance,
            "min_available_capacity": min_capacity,
        }
