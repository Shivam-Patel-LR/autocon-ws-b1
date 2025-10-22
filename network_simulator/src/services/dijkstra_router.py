"""
Capacity-aware Dijkstra routing for Stage B of service generation.
Uses custom cost function that favors high-residual-capacity edges.
"""

import heapq
import networkx as nx
import numpy as np
from math import radians, sin, cos, asin, sqrt
from typing import List, Dict, Tuple, Optional, Set


class CapacityAwareDijkstra:
    """
    Implements Dijkstra's shortest path algorithm with capacity-aware cost function.

    Cost function: cost(e) = (r_e / D)^(-p) + noise
    - Lower cost for edges with higher residual capacity
    - Noise breaks ties randomly for equal-cost paths
    """

    def __init__(self, rng: np.random.RandomState, node_coordinates: Dict[str, Tuple[float, float]] = None):
        """
        Initialize the Dijkstra router.

        Args:
            rng: Random number generator for reproducible tie-breaking noise
            node_coordinates: Dictionary mapping node names to (lat, long) tuples
        """
        self.rng = rng
        self.node_coordinates = node_coordinates or {}

    def compute_path(
        self,
        graph: nx.Graph,
        source: str,
        target: str,
        residuals: Dict[Tuple[str, str], float],
        demand: float,
        p_exponent: float = 1.5,
        noise_delta: float = 0.01
    ) -> Optional[List[str]]:
        """
        Compute shortest path using capacity-aware cost function.

        Args:
            graph: NetworkX graph
            source: Source node name
            target: Target node name
            residuals: Dictionary mapping edge tuples to residual capacities
            demand: Fixed demand D
            p_exponent: Exponent p in cost function (r_e/D)^(-p)
            noise_delta: Uniform noise range [-delta, +delta] for tie-breaking

        Returns:
            List of node names forming path from source to target, or None if no path exists
        """
        # Check basic validity
        if source not in graph.nodes() or target not in graph.nodes():
            return None

        if source == target:
            return [source]

        # Check connectivity using threshold graph (only edges with r_e >= D)
        if not self.check_connectivity(graph, source, target, residuals, demand):
            return None

        # Initialize Dijkstra data structures
        distances = {node: float('inf') for node in graph.nodes()}
        distances[source] = 0.0
        predecessors = {node: None for node in graph.nodes()}
        visited = set()

        # Priority queue: (distance, node)
        heap = [(0.0, source)]

        while heap:
            current_dist, current_node = heapq.heappop(heap)

            # Skip if already visited
            if current_node in visited:
                continue

            visited.add(current_node)

            # Found target
            if current_node == target:
                break

            # Explore neighbors
            for neighbor in graph.neighbors(current_node):
                if neighbor in visited:
                    continue

                # Get edge residual
                edge_key = tuple(sorted([current_node, neighbor]))
                residual = residuals.get(edge_key, 0.0)

                # Only consider edges with sufficient residual capacity
                if residual < demand:
                    continue

                # Compute edge cost: cost(e) = (r_e / D)^(-p) + noise
                normalized_residual = residual / demand
                if normalized_residual <= 0:
                    continue  # Should not happen given check above

                base_cost = normalized_residual ** (-p_exponent)

                # Add uniform tie-breaking noise
                noise = self.rng.uniform(-noise_delta, noise_delta)
                edge_cost = base_cost + noise

                # Update distance if we found a better path
                new_dist = current_dist + edge_cost

                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    predecessors[neighbor] = current_node
                    heapq.heappush(heap, (new_dist, neighbor))

        # Reconstruct path
        if distances[target] == float('inf'):
            return None  # No path found

        path = []
        current = target
        while current is not None:
            path.append(current)
            current = predecessors[current]

        path.reverse()

        # Verify path starts at source
        if path[0] != source:
            return None

        return path

    def check_connectivity(
        self,
        graph: nx.Graph,
        source: str,
        target: str,
        residuals: Dict[Tuple[str, str], float],
        demand: float
    ) -> bool:
        """
        Check if source and target are in same connected component of threshold graph G_D.

        Uses BFS to check reachability using only edges with r_e >= D.

        Args:
            graph: NetworkX graph
            source: Source node name
            target: Target node name
            residuals: Dictionary mapping edge tuples to residual capacities
            demand: Fixed demand D

        Returns:
            True if source can reach target using edges with r_e >= D
        """
        if source == target:
            return True

        # BFS from source
        visited = {source}
        queue = [source]

        while queue:
            current = queue.pop(0)

            for neighbor in graph.neighbors(current):
                if neighbor in visited:
                    continue

                # Check edge capacity
                edge_key = tuple(sorted([current, neighbor]))
                residual = residuals.get(edge_key, 0.0)

                if residual < demand:
                    continue  # Edge not available

                visited.add(neighbor)

                if neighbor == target:
                    return True

                queue.append(neighbor)

        return False

    @staticmethod
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
        # Earth's radius in kilometers
        R = 6371.0

        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        return R * c

    def get_path_distance(
        self,
        graph: nx.Graph,
        path: List[str]
    ) -> float:
        """
        Calculate total geographic distance of path using Haversine formula.

        Args:
            graph: NetworkX graph
            path: List of nodes in path

        Returns:
            Total distance in kilometers
        """
        total_distance = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]

            # Calculate distance using node coordinates
            if u in self.node_coordinates and v in self.node_coordinates:
                lat1, lon1 = self.node_coordinates[u]
                lat2, lon2 = self.node_coordinates[v]
                total_distance += self.haversine_distance(lat1, lon1, lat2, lon2)

        return total_distance

    def get_path_stats(
        self,
        graph: nx.Graph,
        path: List[str],
        residuals: Dict[Tuple[str, str], float]
    ) -> Dict:
        """
        Get detailed statistics about a path.

        Args:
            graph: NetworkX graph
            path: List of nodes in path
            residuals: Dictionary mapping edge tuples to residual capacities

        Returns:
            Dictionary with path statistics
        """
        if not path or len(path) < 2:
            return {
                "hop_count": 0,
                "total_distance": 0.0,
                "min_residual": 0.0,
                "avg_residual": 0.0,
                "edges": []
            }

        edges = []
        residual_values = []

        for i in range(len(path) - 1):
            edge_key = tuple(sorted([path[i], path[i + 1]]))
            residual = residuals.get(edge_key, 0.0)
            residual_values.append(residual)
            edges.append(edge_key)

        return {
            "hop_count": len(path) - 1,
            "total_distance": self.get_path_distance(graph, path),
            "min_residual": min(residual_values) if residual_values else 0.0,
            "avg_residual": sum(residual_values) / len(residual_values) if residual_values else 0.0,
            "edges": edges
        }
