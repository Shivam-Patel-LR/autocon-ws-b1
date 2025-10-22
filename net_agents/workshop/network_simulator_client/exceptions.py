"""
Custom exceptions for the Network Simulator Client.

This module defines a comprehensive exception hierarchy for handling
various error conditions when interacting with the Network Simulator API.
"""
from typing import Optional, Dict, Any


class NetworkSimulatorError(Exception):
    """
    Base exception class for all Network Simulator Client errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if applicable)
        response_data: Raw response data from the API (if available)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class APIConnectionError(NetworkSimulatorError):
    """
    Raised when unable to connect to the Network Simulator API.

    This typically indicates network issues, incorrect base URL,
    or the API server being unavailable.
    """
    pass


class APITimeoutError(NetworkSimulatorError):
    """
    Raised when an API request times out.

    This occurs when the server doesn't respond within the configured timeout period.
    """
    pass


class ValidationError(NetworkSimulatorError):
    """
    Raised when request data fails validation (HTTP 400).

    This includes:
    - Invalid field values
    - Missing required fields
    - Type mismatches
    - Constraint violations (e.g., capacity <= 0)
    """
    pass


class ResourceNotFoundError(NetworkSimulatorError):
    """
    Base class for resource not found errors (HTTP 404).
    """
    pass


class NodeNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested node does not exist.

    Attributes:
        node_uuid: The UUID of the node that was not found
    """

    def __init__(
        self,
        message: str,
        node_uuid: Optional[str] = None,
        status_code: int = 404,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.node_uuid = node_uuid
        super().__init__(message, status_code, response_data)


class EdgeNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested edge does not exist.

    Attributes:
        edge_uuid: The UUID of the edge that was not found
    """

    def __init__(
        self,
        message: str,
        edge_uuid: Optional[str] = None,
        status_code: int = 404,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.edge_uuid = edge_uuid
        super().__init__(message, status_code, response_data)


class ServiceNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested service does not exist.

    Attributes:
        service_uuid: The UUID of the service that was not found
    """

    def __init__(
        self,
        message: str,
        service_uuid: Optional[str] = None,
        status_code: int = 404,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.service_uuid = service_uuid
        super().__init__(message, status_code, response_data)


class ResourceConflictError(NetworkSimulatorError):
    """
    Raised when a resource operation conflicts with existing data (HTTP 409).

    This includes:
    - Attempting to delete a node that is referenced by edges or services
    - Attempting to delete an edge that is referenced by services
    - Creating duplicate resources
    """
    pass


class RouteNotFoundError(NetworkSimulatorError):
    """
    Raised when no feasible route can be found between nodes (HTTP 422).

    This occurs when:
    - No path exists between the source and destination nodes
    - All paths lack sufficient capacity for the requested demand
    """

    def __init__(
        self,
        message: str,
        source_node_uuid: Optional[str] = None,
        destination_node_uuid: Optional[str] = None,
        demand_gbps: Optional[float] = None,
        status_code: int = 422,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.source_node_uuid = source_node_uuid
        self.destination_node_uuid = destination_node_uuid
        self.demand_gbps = demand_gbps
        super().__init__(message, status_code, response_data)


class CapacityViolationError(NetworkSimulatorError):
    """
    Raised when an operation would violate capacity constraints.

    This is typically used when capacity violations are detected
    during service creation or capacity analysis.
    """

    def __init__(
        self,
        message: str,
        edge_uuid: Optional[str] = None,
        capacity_gbps: Optional[float] = None,
        demand_gbps: Optional[float] = None,
        overage: Optional[float] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.edge_uuid = edge_uuid
        self.capacity_gbps = capacity_gbps
        self.demand_gbps = demand_gbps
        self.overage = overage
        super().__init__(message, status_code, response_data)


class AuthenticationError(NetworkSimulatorError):
    """
    Raised when authentication fails (HTTP 401).

    Note: Current API version doesn't require authentication,
    but this is included for future compatibility.
    """
    pass


class AuthorizationError(NetworkSimulatorError):
    """
    Raised when the client lacks permission for an operation (HTTP 403).

    Note: Current API version doesn't implement authorization,
    but this is included for future compatibility.
    """
    pass


class RateLimitError(NetworkSimulatorError):
    """
    Raised when the API rate limit is exceeded (HTTP 429).

    Note: Current API version doesn't implement rate limiting,
    but this is included for future compatibility.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        status_code: int = 429,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code, response_data)


class ServerError(NetworkSimulatorError):
    """
    Raised when the API returns a server error (HTTP 5xx).

    This indicates an issue with the API server itself.
    """
    pass


def exception_from_response(status_code: int, message: str, response_data: Optional[Dict[str, Any]] = None) -> NetworkSimulatorError:
    """
    Create an appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code
        message: Error message
        response_data: Raw response data from the API

    Returns:
        Appropriate exception instance
    """
    exception_map = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: ResourceNotFoundError,
        409: ResourceConflictError,
        422: RouteNotFoundError,
        429: RateLimitError,
    }

    if status_code >= 500:
        return ServerError(message, status_code, response_data)

    exception_class = exception_map.get(status_code, NetworkSimulatorError)
    return exception_class(message, status_code, response_data)
