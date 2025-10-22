"""
Service data class for representing network services with routing paths.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


@dataclass
class Service:
    """
    Represents a network service routed through the topology.

    Attributes:
        service_id: Unique identifier (e.g., "SVC-001")
        name: Human-readable service name
        source: Source node name
        destination: Destination node name
        path: Ordered list of node names from source to destination
        demand_gbps: Bandwidth demand in Gbps
        hop_count: Number of hops (len(path) - 1)
        total_distance_km: Total geographic distance in kilometers
        timestamp: ISO 8601 timestamp (randomized in 2020-2025 range)
        _routing_stage: Internal tracking of routing stage (not exported)
    """

    service_id: str
    name: str
    source: str
    destination: str
    path: List[str]
    demand_gbps: float
    hop_count: int = field(init=False)
    total_distance_km: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    _routing_stage: str = field(default="stage_b", repr=False)

    def __post_init__(self):
        """Calculate derived fields after initialization."""
        self.hop_count = len(self.path) - 1
        self.validate()

    def validate(self) -> None:
        """
        Validate service data for correctness.

        Raises:
            ValueError: If service data is invalid
        """
        # Path must have at least 2 nodes (source and destination)
        if len(self.path) < 2:
            raise ValueError(f"Path must have at least 2 nodes, got {len(self.path)}")

        # First node must be source
        if self.path[0] != self.source:
            raise ValueError(f"Path first node '{self.path[0]}' must match source '{self.source}'")

        # Last node must be destination
        if self.path[-1] != self.destination:
            raise ValueError(f"Path last node '{self.path[-1]}' must match destination '{self.destination}'")

        # Path must be simple (no repeated nodes)
        if len(self.path) != len(set(self.path)):
            raise ValueError(f"Path must be simple (no repeated nodes): {self.path}")

        # Source and destination must be distinct
        if self.source == self.destination:
            raise ValueError(f"Source and destination must be distinct, got '{self.source}'")

        # Demand must be positive
        if self.demand_gbps <= 0:
            raise ValueError(f"Demand must be positive, got {self.demand_gbps}")

        # Distance must be non-negative
        if self.total_distance_km < 0:
            raise ValueError(f"Distance must be non-negative, got {self.total_distance_km}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert service to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the service
        """
        return {
            "service_id": self.service_id,
            "name": self.name,
            "source": self.source,
            "destination": self.destination,
            "path": self.path,
            "demand_gbps": self.demand_gbps,
            "hop_count": self.hop_count,
            "total_distance_km": round(self.total_distance_km, 2),
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """
        Create Service from dictionary.

        Args:
            data: Dictionary containing service data

        Returns:
            Service instance
        """
        return cls(
            service_id=data["service_id"],
            name=data["name"],
            source=data["source"],
            destination=data["destination"],
            path=data["path"],
            demand_gbps=data["demand_gbps"],
            total_distance_km=data.get("total_distance_km", 0.0),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            _routing_stage=data.get("_routing_stage", "stage_b")
        )

    @staticmethod
    def generate_random_timestamp(service_index: int, base_seed: int = 42) -> str:
        """
        Generate a random timestamp between 2020-01-01 and 2025-12-31.

        Args:
            service_index: Index of the service (for reproducibility)
            base_seed: Base random seed

        Returns:
            ISO 8601 formatted timestamp string
        """
        # Use service index with base seed for reproducibility
        rng = random.Random(base_seed + service_index)

        # Define date range: 2020-01-01 to 2025-12-31
        start_date = datetime(2020, 1, 1, 0, 0, 0)
        end_date = datetime(2025, 12, 31, 23, 59, 59)

        # Calculate random timestamp
        time_delta = end_date - start_date
        random_days = rng.randint(0, time_delta.days)
        random_seconds = rng.randint(0, 86399)  # 0 to 86399 seconds in a day

        random_timestamp = start_date + timedelta(days=random_days, seconds=random_seconds)

        return random_timestamp.isoformat() + "Z"

    def get_edges(self) -> List[tuple]:
        """
        Get list of edges used by this service path.

        Returns:
            List of (node1, node2) tuples representing edges in path
        """
        edges = []
        for i in range(len(self.path) - 1):
            # Always store edges in sorted order for consistency
            edge = tuple(sorted([self.path[i], self.path[i + 1]]))
            edges.append(edge)
        return edges

    def __repr__(self) -> str:
        """String representation of the Service."""
        return (f"Service(id='{self.service_id}', "
                f"{self.source} → {self.destination}, "
                f"hops={self.hop_count}, "
                f"demand={self.demand_gbps}Gbps)")

    def __str__(self) -> str:
        """Human-readable string representation."""
        path_str = " → ".join(self.path)
        return f"{self.service_id}: {path_str} ({self.demand_gbps} Gbps)"
