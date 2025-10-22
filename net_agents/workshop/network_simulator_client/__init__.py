"""
Network Simulator Client SDK

A comprehensive Python client for the Network Simulator API.
Provides both synchronous and asynchronous interfaces for all API operations.
"""

__version__ = "0.1.0"

from .client import NetworkSimulatorClient
from .exceptions import (
    NetworkSimulatorError,
    APIConnectionError,
    APITimeoutError,
    ValidationError,
    ResourceNotFoundError,
    NodeNotFoundError,
    EdgeNotFoundError,
    ServiceNotFoundError,
    ResourceConflictError,
    RouteNotFoundError,
    CapacityViolationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServerError,
)
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

__all__ = [
    "__version__",
    # Client
    "NetworkSimulatorClient",
    # Exceptions
    "NetworkSimulatorError",
    "APIConnectionError",
    "APITimeoutError",
    "ValidationError",
    "ResourceNotFoundError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "ServiceNotFoundError",
    "ResourceConflictError",
    "RouteNotFoundError",
    "CapacityViolationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ServerError",
    # Models
    "HealthResponse",
    "NodeCreate",
    "NodeUpdate",
    "NodeResponse",
    "EdgeCreate",
    "EdgeResponse",
    "ServiceCreate",
    "ServiceResponse",
    "RouteRequest",
    "RouteResponse",
    "DatabaseStatsResponse",
    "EdgeUtilizationResponse",
    "CapacityViolationResponse",
]
