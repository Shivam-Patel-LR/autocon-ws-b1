"""
A* routing algorithm with capacity constraints for network path finding.

Uses geographic distance (Haversine) as both cost and heuristic.
Capacity constraints act as edge filters, not cost components.
"""

import heapq
import networkx as nx
from math import radians, sin, cos, asin, sqrt
from typing import List, Dict, Tuple, Optional
import time


class AStarRouter:
    """
    A* pathfinding algorithm for network routing.

    Finds the shortest geographic path between two nodes while respecting
    capacity constraints. Uses Haversine distance for both actual cost and
    heuristic estimation.

    Algorithm:
        - Cost g(n): Sum of actual hop-to-hop distances from source to n
        - Heuristic h(n): Haversine distance from n to target (admissible)
        - f(n) = g(n) + h(n)
        - Edge filter: Only use edges with residual_capacity >= demand
    """

    def __init__(self, node_coordinates: Dict[str, Tuple[float, float]]):
        """
        Initialize A* router.

        Args:
            node_coordinates: Dictionary mapping node UUIDs to (latitude, longitude)
        """
        self.node_coordinates = node_coordinates

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
        R = 6371.0  # Earth's radius in kilometers

        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        return R * c

    def compute_route(
        self,
        graph: nx.Graph,
        source_uuid: str,
        destination_uuid: str,
        residual_capacities: Dict[str, float],
        demand_gbps: float = 5.0
    ) -> Optional[Dict]:
        """
        Compute shortest geographic path using A* with capacity constraints.

        Args:
            graph: NetworkX graph with nodes as UUIDs and edges with 'uuid' attribute
            source_uuid: Source node UUID
            destination_uuid: Destination node UUID
            residual_capacities: Dict mapping edge UUIDs to available capacity
            demand_gbps: Required bandwidth for this route

        Returns:
            Dictionary with route details:
                - path_node_uuids: List of node UUIDs in path
                - path_edge_uuids: List of edge UUIDs in path
                - total_distance_km: Total path distance
                - hop_count: Number of hops
                - min_available_capacity: Bottleneck capacity along path
                - computation_time_ms: Time taken to compute route
            Returns None if no feasible path exists
        """
        start_time = time.time()

        # Validate inputs
        if source_uuid not in graph.nodes():
            return None
        if destination_uuid not in graph.nodes():
            return None

        # Handle trivial case
        if source_uuid == destination_uuid:
            return {
                'path_node_uuids': [source_uuid],
                'path_edge_uuids': [],
                'total_distance_km': 0.0,
                'hop_count': 0,
                'min_available_capacity': float('inf'),
                'computation_time_ms': (time.time() - start_time) * 1000
            }

        # Get coordinates
        if source_uuid not in self.node_coordinates:
            return None
        if destination_uuid not in self.node_coordinates:
            return None

        dest_lat, dest_lon = self.node_coordinates[destination_uuid]

        # A* data structures
        # g_score[node] = actual cost from source to node
        g_score = {source_uuid: 0.0}

        # f_score[node] = g_score[node] + h(node)
        # h(node) = haversine distance from node to destination
        source_lat, source_lon = self.node_coordinates[source_uuid]
        h_start = self.haversine_distance(source_lat, source_lon, dest_lat, dest_lon)
        f_score = {source_uuid: h_start}

        # Priority queue: (f_score, node_uuid)
        open_set = [(f_score[source_uuid], source_uuid)]

        # Track predecessors for path reconstruction
        came_from = {}

        # Track which edge was used to reach each node
        edge_used = {}

        # Closed set
        closed_set = set()

        while open_set:
            current_f, current_node = heapq.heappop(open_set)

            # Skip if already processed
            if current_node in closed_set:
                continue

            # Mark as processed
            closed_set.add(current_node)

            # Check if we reached the destination
            if current_node == destination_uuid:
                # Reconstruct path
                path_nodes = []
                path_edges = []
                node = destination_uuid

                while node in came_from:
                    path_nodes.append(node)
                    if node in edge_used:
                        path_edges.append(edge_used[node])
                    node = came_from[node]

                path_nodes.append(source_uuid)
                path_nodes.reverse()
                path_edges.reverse()

                # Calculate minimum capacity along path
                min_capacity = float('inf')
                for edge_uuid in path_edges:
                    capacity = residual_capacities.get(edge_uuid, 0.0)
                    min_capacity = min(min_capacity, capacity)

                computation_time = (time.time() - start_time) * 1000

                return {
                    'path_node_uuids': path_nodes,
                    'path_edge_uuids': path_edges,
                    'total_distance_km': g_score[destination_uuid],
                    'hop_count': len(path_edges),
                    'min_available_capacity': min_capacity,
                    'computation_time_ms': computation_time
                }

            # Explore neighbors
            current_lat, current_lon = self.node_coordinates[current_node]

            for neighbor in graph.neighbors(current_node):
                if neighbor in closed_set:
                    continue

                # Get edge data
                edge_data = graph.get_edge_data(current_node, neighbor)
                if not edge_data:
                    continue

                edge_uuid = edge_data.get('uuid')
                if not edge_uuid:
                    continue

                # Check capacity constraint
                residual = residual_capacities.get(edge_uuid, 0.0)
                if residual < demand_gbps:
                    continue  # Insufficient capacity, skip this edge

                # Calculate actual cost to reach neighbor
                if neighbor not in self.node_coordinates:
                    continue

                neighbor_lat, neighbor_lon = self.node_coordinates[neighbor]
                edge_distance = self.haversine_distance(
                    current_lat, current_lon,
                    neighbor_lat, neighbor_lon
                )

                tentative_g_score = g_score[current_node] + edge_distance

                # If this is a better path to neighbor, update it
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current_node
                    edge_used[neighbor] = edge_uuid
                    g_score[neighbor] = tentative_g_score

                    # Calculate heuristic (remaining distance estimate)
                    h_score = self.haversine_distance(
                        neighbor_lat, neighbor_lon,
                        dest_lat, dest_lon
                    )

                    f_score[neighbor] = tentative_g_score + h_score
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # No path found
        return None

    def find_multiple_paths(
        self,
        graph: nx.Graph,
        source_uuid: str,
        destination_uuid: str,
        residual_capacities: Dict[str, float],
        demand_gbps: float = 5.0,
        num_paths: int = 3
    ) -> List[Dict]:
        """
        Find multiple diverse paths between source and destination.

        Uses edge penalty approach: after finding a path, temporarily penalize
        edges in that path to encourage diversity.

        Args:
            graph: NetworkX graph
            source_uuid: Source node UUID
            destination_uuid: Destination node UUID
            residual_capacities: Available capacity per edge
            demand_gbps: Required bandwidth
            num_paths: Number of alternative paths to find

        Returns:
            List of route dictionaries (sorted by distance)
        """
        paths = []
        edge_penalties = {}  # Track how many times each edge was used

        for i in range(num_paths):
            # Adjust residual capacities based on penalties
            adjusted_capacities = residual_capacities.copy()

            # Apply penalties (reduce effective capacity for heavily used edges)
            for edge_uuid, penalty in edge_penalties.items():
                if edge_uuid in adjusted_capacities:
                    # Reduce capacity by 20% per use to discourage reuse
                    adjusted_capacities[edge_uuid] *= (0.8 ** penalty)

            # Find path with adjusted capacities
            route = self.compute_route(
                graph, source_uuid, destination_uuid,
                adjusted_capacities, demand_gbps
            )

            if route is None:
                break  # No more paths available

            paths.append(route)

            # Add penalties to edges in this path
            for edge_uuid in route['path_edge_uuids']:
                edge_penalties[edge_uuid] = edge_penalties.get(edge_uuid, 0) + 1

        return paths
