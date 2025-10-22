"""
Network Element class for the network simulator.
Represents a simplified network node that handles routing, switching, and multiplexing.
"""

from typing import Optional


class NetworkElement:
    """
    Represents a network element (node) in the network.

    Attributes:
        uuid (str): Unique UUID identifier for this network element
        name (str): Human-readable name/identifier of the network element
        lat (float): Latitude coordinate
        long (float): Longitude coordinate
        vendor (str): Vendor/manufacturer of the network element
        capacity_gbps (int): Total switching/routing capacity in Gbps
    """

    def __init__(
        self,
        name: str,
        lat: float,
        long: float,
        vendor: str,
        capacity_gbps: int,
        node_uuid: Optional[str] = None
    ):
        """
        Initialize a NetworkElement.

        Args:
            name: Human-readable identifier for this network element
            lat: Latitude coordinate
            long: Longitude coordinate
            vendor: Vendor/manufacturer name
            capacity_gbps: Total capacity in Gbps
            node_uuid: Optional UUID string (if None, will be set by registry)
        """
        self.uuid = node_uuid  # Will be set by registry if None
        self.name = name
        self.lat = lat
        self.long = long
        self.vendor = vendor
        self.capacity_gbps = capacity_gbps

    def __repr__(self) -> str:
        """String representation of the NetworkElement."""
        return f"NetworkElement(name='{self.name}', location=({self.lat}, {self.long}), capacity={self.capacity_gbps}Gbps)"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name} [{self.vendor}] - {self.capacity_gbps} Gbps"
