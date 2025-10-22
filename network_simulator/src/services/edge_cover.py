"""
Edge cover algorithm for Stage A of service routing.
Computes minimum edge cover to guarantee every node is an endpoint of at least one service.
"""

import networkx as nx
from typing import List, Tuple, Set


class EdgeCoverBuilder:
    """
    Builds a minimum edge cover for a graph to ensure all vertices are covered.

    An edge cover F ⊆ E is a set of edges such that every vertex is incident to
    at least one edge in F. A minimum edge cover has the smallest possible size.

    For a graph G with no isolated vertices, a minimum edge cover can be constructed as:
        |F| = n - |M|
    where M is a maximum matching and n is the number of vertices.
    """

    def __init__(self):
        """Initialize the EdgeCoverBuilder."""
        pass

    def find_edge_cover(
        self,
        graph: nx.Graph,
        available_edges: Set[Tuple[str, str]] = None
    ) -> List[Tuple[str, str]]:
        """
        Find a minimum edge cover for the graph.

        Args:
            graph: NetworkX graph (undirected)
            available_edges: Optional set of edges to restrict search to.
                           If None, uses all edges in graph.
                           Format: Set of (node1, node2) tuples in sorted order.

        Returns:
            List of edges forming an edge cover (each edge as sorted tuple)

        Raises:
            ValueError: If graph has isolated vertices (no edge cover exists)
        """
        # Check for isolated vertices
        isolated = [node for node in graph.nodes() if graph.degree(node) == 0]
        if isolated:
            raise ValueError(
                f"Cannot create edge cover: graph has {len(isolated)} isolated vertices: {isolated}"
            )

        # If specific edges are provided, create subgraph
        if available_edges is not None:
            # Create subgraph with only available edges
            subgraph = nx.Graph()
            subgraph.add_nodes_from(graph.nodes())
            for edge in available_edges:
                if graph.has_edge(*edge):
                    subgraph.add_edge(*edge, **graph.edges[edge])

            # Check for isolated vertices in subgraph
            isolated_in_subgraph = [node for node in subgraph.nodes() if subgraph.degree(node) == 0]
            if isolated_in_subgraph:
                raise ValueError(
                    f"Cannot create edge cover with available edges: "
                    f"{len(isolated_in_subgraph)} vertices have degree 0: {isolated_in_subgraph}"
                )
            working_graph = subgraph
        else:
            working_graph = graph

        # Compute maximum matching using NetworkX
        matching = nx.max_weight_matching(working_graph, maxcardinality=True)

        # Convert matching to set of edges (in sorted order)
        matched_edges = set()
        matched_vertices = set()
        for u, v in matching:
            edge = tuple(sorted([u, v]))
            matched_edges.add(edge)
            matched_vertices.add(u)
            matched_vertices.add(v)

        # Start building edge cover with matching
        edge_cover = list(matched_edges)

        # Find unmatched vertices
        all_vertices = set(working_graph.nodes())
        unmatched_vertices = all_vertices - matched_vertices

        # For each unmatched vertex, add one incident edge
        for vertex in unmatched_vertices:
            # Get all edges incident to this vertex
            incident_edges = []
            for neighbor in working_graph.neighbors(vertex):
                edge = tuple(sorted([vertex, neighbor]))
                # Don't add edge if already in cover
                if edge not in matched_edges:
                    incident_edges.append(edge)

            if not incident_edges:
                # This shouldn't happen if we checked for isolated vertices
                raise ValueError(f"No incident edges found for vertex {vertex}")

            # Add the first available incident edge
            # (Could use a heuristic here, but any will work)
            edge_cover.append(incident_edges[0])
            matched_edges.add(incident_edges[0])

        return edge_cover

    def verify_coverage(
        self,
        graph: nx.Graph,
        edge_cover: List[Tuple[str, str]]
    ) -> bool:
        """
        Verify that the edge cover actually covers all vertices.

        Args:
            graph: NetworkX graph
            edge_cover: List of edges forming the proposed edge cover

        Returns:
            True if all vertices are covered, False otherwise
        """
        covered_vertices = set()
        for u, v in edge_cover:
            covered_vertices.add(u)
            covered_vertices.add(v)

        all_vertices = set(graph.nodes())
        return all_vertices == covered_vertices

    def get_coverage_stats(
        self,
        graph: nx.Graph,
        edge_cover: List[Tuple[str, str]]
    ) -> dict:
        """
        Get detailed statistics about the edge cover.

        Args:
            graph: NetworkX graph
            edge_cover: List of edges forming the edge cover

        Returns:
            Dictionary with coverage statistics
        """
        covered_vertices = set()
        vertex_coverage_count = {}

        for u, v in edge_cover:
            covered_vertices.add(u)
            covered_vertices.add(v)
            vertex_coverage_count[u] = vertex_coverage_count.get(u, 0) + 1
            vertex_coverage_count[v] = vertex_coverage_count.get(v, 0) + 1

        all_vertices = set(graph.nodes())
        uncovered_vertices = all_vertices - covered_vertices

        return {
            "total_vertices": len(all_vertices),
            "covered_vertices": len(covered_vertices),
            "uncovered_vertices": len(uncovered_vertices),
            "edge_cover_size": len(edge_cover),
            "min_coverage": min(vertex_coverage_count.values()) if vertex_coverage_count else 0,
            "max_coverage": max(vertex_coverage_count.values()) if vertex_coverage_count else 0,
            "avg_coverage": sum(vertex_coverage_count.values()) / len(vertex_coverage_count) if vertex_coverage_count else 0,
            "is_valid_cover": len(uncovered_vertices) == 0
        }


def create_threshold_graph(
    graph: nx.Graph,
    residuals: dict,
    demand: float
) -> Tuple[nx.Graph, Set[Tuple[str, str]]]:
    """
    Create threshold residual graph G_D where only edges with r_e >= D are included.

    Args:
        graph: Original NetworkX graph
        residuals: Dictionary mapping edge tuples to residual capacities
        demand: Fixed demand value D

    Returns:
        Tuple of (threshold_graph, available_edges_set)
    """
    threshold_graph = nx.Graph()
    threshold_graph.add_nodes_from(graph.nodes())

    available_edges = set()

    for edge in graph.edges():
        edge_key = tuple(sorted(edge))
        residual = residuals.get(edge_key, 0.0)

        if residual >= demand:
            threshold_graph.add_edge(*edge, **graph.edges[edge])
            available_edges.add(edge_key)

    return threshold_graph, available_edges
