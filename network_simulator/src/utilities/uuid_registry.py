"""
UUID registry system for managing unique identifiers for nodes and edges.
Provides bidirectional mappings and persistent storage.
"""

import uuid
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, Any


class NodeRegistry:
    """
    Registry for managing node UUIDs and metadata.

    Provides bidirectional mapping between node names and UUIDs,
    along with full node metadata storage.
    """

    def __init__(self):
        """Initialize empty node registry."""
        self.name_to_uuid: Dict[str, str] = {}
        self.uuid_to_info: Dict[str, Dict[str, Any]] = {}

    def register_node(
        self,
        name: str,
        lat: float,
        long: float,
        vendor: str,
        capacity_gbps: float,
        node_uuid: Optional[str] = None
    ) -> str:
        """
        Register a node and return its UUID.

        If the node name already exists, returns the existing UUID.
        If uuid is provided, uses that; otherwise generates a new UUID.

        Args:
            name: Node name (e.g., "NYC-Manhattan")
            lat: Latitude
            long: Longitude
            vendor: Vendor name
            capacity_gbps: Node capacity in Gbps
            node_uuid: Optional UUID string to use (for loading from file)

        Returns:
            UUID string for the node
        """
        # Return existing UUID if already registered
        if name in self.name_to_uuid:
            return self.name_to_uuid[name]

        # Generate new UUID or use provided one
        if node_uuid is None:
            node_uuid = str(uuid.uuid4())

        # Store mappings
        self.name_to_uuid[name] = node_uuid
        self.uuid_to_info[node_uuid] = {
            "name": name,
            "lat": lat,
            "long": long,
            "vendor": vendor,
            "capacity_gbps": capacity_gbps
        }

        return node_uuid

    def get_uuid(self, name: str) -> Optional[str]:
        """Get UUID for a node name."""
        return self.name_to_uuid.get(name)

    def get_name(self, node_uuid: str) -> Optional[str]:
        """Get name for a node UUID."""
        info = self.uuid_to_info.get(node_uuid)
        return info["name"] if info else None

    def get_info(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        """Get full metadata for a node UUID."""
        return self.uuid_to_info.get(node_uuid)

    def get_coordinates(self, node_uuid: str) -> Optional[Tuple[float, float]]:
        """Get (lat, long) coordinates for a node UUID."""
        info = self.uuid_to_info.get(node_uuid)
        if info:
            return (info["lat"], info["long"])
        return None

    def get_all_uuids(self) -> list:
        """Get list of all node UUIDs."""
        return list(self.uuid_to_info.keys())

    def get_all_names(self) -> list:
        """Get list of all node names."""
        return list(self.name_to_uuid.keys())

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Export registry to dictionary format.

        Returns:
            Dictionary mapping UUIDs to node info
        """
        return self.uuid_to_info.copy()

    def from_dict(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Load registry from dictionary format.

        Args:
            data: Dictionary mapping UUIDs to node info
        """
        self.uuid_to_info = data.copy()
        self.name_to_uuid = {
            info["name"]: node_uuid
            for node_uuid, info in data.items()
        }

    def export_to_json(self, filepath: str) -> None:
        """Export registry to JSON file."""
        output = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Node registry exported to: {filepath}")

    def load_from_json(self, filepath: str) -> None:
        """Load registry from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.from_dict(data)
        print(f"Node registry loaded from: {filepath}")

    def __len__(self) -> int:
        """Return number of registered nodes."""
        return len(self.uuid_to_info)


class EdgeRegistry:
    """
    Registry for managing edge UUIDs and metadata.

    Provides mapping between edge endpoints (as node UUIDs) and edge UUIDs,
    along with edge metadata storage.
    """

    def __init__(self):
        """Initialize empty edge registry."""
        self.endpoints_to_uuid: Dict[Tuple[str, str], str] = {}
        self.uuid_to_info: Dict[str, Dict[str, Any]] = {}

    def register_edge(
        self,
        node1_uuid: str,
        node2_uuid: str,
        capacity_gbps: float,
        edge_uuid: Optional[str] = None
    ) -> str:
        """
        Register an edge and return its UUID.

        If the edge already exists, returns the existing UUID.
        If uuid is provided, uses that; otherwise generates a new UUID.

        Args:
            node1_uuid: UUID of first endpoint node
            node2_uuid: UUID of second endpoint node
            capacity_gbps: Edge capacity in Gbps
            edge_uuid: Optional UUID string to use (for loading from file)

        Returns:
            UUID string for the edge
        """
        # Create canonical edge key (sorted tuple)
        edge_key = tuple(sorted([node1_uuid, node2_uuid]))

        # Return existing UUID if already registered
        if edge_key in self.endpoints_to_uuid:
            return self.endpoints_to_uuid[edge_key]

        # Generate new UUID or use provided one
        if edge_uuid is None:
            edge_uuid = str(uuid.uuid4())

        # Store mappings (always store in canonical form)
        self.endpoints_to_uuid[edge_key] = edge_uuid
        self.uuid_to_info[edge_uuid] = {
            "node_1_uuid": edge_key[0],
            "node_2_uuid": edge_key[1],
            "capacity_gbps": capacity_gbps
        }

        return edge_uuid

    def get_uuid(self, node1_uuid: str, node2_uuid: str) -> Optional[str]:
        """Get UUID for an edge given its endpoint UUIDs."""
        edge_key = tuple(sorted([node1_uuid, node2_uuid]))
        return self.endpoints_to_uuid.get(edge_key)

    def get_info(self, edge_uuid: str) -> Optional[Dict[str, Any]]:
        """Get full metadata for an edge UUID."""
        return self.uuid_to_info.get(edge_uuid)

    def get_endpoints(self, edge_uuid: str) -> Optional[Tuple[str, str]]:
        """Get endpoint node UUIDs for an edge UUID."""
        info = self.uuid_to_info.get(edge_uuid)
        if info:
            return (info["node_1_uuid"], info["node_2_uuid"])
        return None

    def get_all_uuids(self) -> list:
        """Get list of all edge UUIDs."""
        return list(self.uuid_to_info.keys())

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Export registry to dictionary format.

        Returns:
            Dictionary mapping UUIDs to edge info
        """
        return self.uuid_to_info.copy()

    def from_dict(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Load registry from dictionary format.

        Args:
            data: Dictionary mapping UUIDs to edge info
        """
        self.uuid_to_info = data.copy()
        self.endpoints_to_uuid = {
            tuple(sorted([info["node_1_uuid"], info["node_2_uuid"]])): edge_uuid
            for edge_uuid, info in data.items()
        }

    def export_to_json(self, filepath: str) -> None:
        """Export registry to JSON file."""
        output = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Edge registry exported to: {filepath}")

    def load_from_json(self, filepath: str) -> None:
        """Load registry from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.from_dict(data)
        print(f"Edge registry loaded from: {filepath}")

    def __len__(self) -> int:
        """Return number of registered edges."""
        return len(self.uuid_to_info)
