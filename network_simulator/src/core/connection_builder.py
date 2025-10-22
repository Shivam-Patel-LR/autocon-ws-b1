"""
Connection Builder module for creating node-to-node connections.
Implements a three-phase capacity-aware graph construction algorithm.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from core.network_element import NetworkElement


class ConnectionBuilder:
    """
    Builds network connections using a three-phase algorithm:
    - Phase I: Capacity-aware spanning tree (connectivity skeleton)
    - Phase II: Greedy augmentation toward hub-and-spoke structure
    - Phase III: Optional local spokes for non-hub nodes
    """

    def __init__(
        self,
        gamma: float = 1.5,
        beta: float = 2.0,
        eta: float = 0.4,
        target_edges: int = 250,
        noise_factor: float = 0.01,
        random_seed: Optional[int] = 42,
        # Alpha function parameters
        alpha_base_phase2: float = 0.25,
        alpha_coefficient_phase2: float = 0.25,
        alpha_base_phase3: float = 0.25,
        alpha_coefficient_phase3: float = 0.25,
        # Graph construction parameters
        min_distance_threshold: float = 0.001,
        non_hub_threshold: float = 0.75,
        spokes_per_node: int = 2,
        capacity_tolerance: float = 1e-6
    ):
        """
        Initialize the ConnectionBuilder.

        Args:
            gamma: Capacity importance in preference score (typical: 1-2)
            beta: Distance importance in preference score (typical: 1-3)
            eta: Weight fraction for Phase I edges (must be in (0, 0.5])
            target_edges: Target number of edges to create (200-300)
            noise_factor: Small random noise to add for organic variation
            random_seed: Random seed for reproducibility (None for random)
            alpha_base_phase2: Base alpha value for Phase II edges
            alpha_coefficient_phase2: Alpha coefficient for Phase II edges
            alpha_base_phase3: Base alpha value for Phase III edges
            alpha_coefficient_phase3: Alpha coefficient for Phase III edges
            min_distance_threshold: Minimum distance to avoid division by zero
            non_hub_threshold: Percentile threshold for non-hub nodes
            spokes_per_node: Max additional connections for non-hub nodes
            capacity_tolerance: Floating-point tolerance for capacity validation
        """
        # Connection algorithm parameters
        self.gamma = gamma
        self.beta = beta
        self.eta = eta
        self.target_edges = target_edges
        self.noise_factor = noise_factor

        # Alpha function parameters
        self.alpha_base_phase2 = alpha_base_phase2
        self.alpha_coefficient_phase2 = alpha_coefficient_phase2
        self.alpha_base_phase3 = alpha_base_phase3
        self.alpha_coefficient_phase3 = alpha_coefficient_phase3

        # Graph construction parameters
        self.min_distance_threshold = min_distance_threshold
        self.non_hub_threshold = non_hub_threshold
        self.spokes_per_node = spokes_per_node
        self.capacity_tolerance = capacity_tolerance

        if random_seed is not None:
            np.random.seed(random_seed)

        # Graph data structures
        self.nodes: List[NetworkElement] = []
        self.edges: List[Dict] = []
        self.residuals: Dict[str, float] = {}
        self.adjacency: Dict[Tuple[str, str], float] = {}

    def calculate_distance(self, node1: NetworkElement, node2: NetworkElement) -> float:
        """
        Calculate Euclidean distance between two nodes based on lat/long.

        Args:
            node1: First network element
            node2: Second network element

        Returns:
            Euclidean distance
        """
        # Simple Euclidean distance in lat/long coordinates
        # For more accuracy, could use Haversine formula for great-circle distance
        dx = node1.long - node2.long
        dy = node1.lat - node2.lat
        return np.sqrt(dx**2 + dy**2)

    def calculate_preference_score(
        self,
        node1: NetworkElement,
        node2: NetworkElement,
        add_noise: bool = True
    ) -> float:
        """
        Calculate preference score S(u,v) = (Cu * Cv)^gamma / d(u,v)^beta

        Higher score = more attractive connection (large capacity, close distance).

        Args:
            node1: First network element
            node2: Second network element
            add_noise: Whether to add small random noise for variation

        Returns:
            Preference score (higher is better)
        """
        distance = self.calculate_distance(node1, node2)

        # Avoid division by zero for very close nodes
        distance = max(distance, self.min_distance_threshold)

        # S(u,v) = (Cu * Cv)^gamma / d(u,v)^beta
        capacity_product = node1.capacity_gbps * node2.capacity_gbps
        score = (capacity_product ** self.gamma) / (distance ** self.beta)

        # Add small noise for organic variation
        if add_noise:
            noise = 1.0 + np.random.uniform(-self.noise_factor, self.noise_factor)
            score *= noise

        return score

    def build_connections(self, network_elements: List[NetworkElement]) -> None:
        """
        Build all connections using the three-phase algorithm.

        Args:
            network_elements: List of network elements to connect
        """
        self.nodes = network_elements
        n = len(self.nodes)

        print(f"\nBuilding connections for {n} nodes...")
        print(f"Parameters: γ={self.gamma}, β={self.beta}, η={self.eta}")
        print(f"Target edges: {self.target_edges}")

        # Initialize residual capacities
        for node in self.nodes:
            self.residuals[node.name] = float(node.capacity_gbps)

        # Calculate max preference score for normalization
        max_score = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                score = self.calculate_preference_score(
                    self.nodes[i],
                    self.nodes[j],
                    add_noise=False
                )
                max_score = max(max_score, score)

        self.max_preference_score = max_score

        # Phase I: Spanning tree
        print("\n[Phase I] Building capacity-aware spanning tree...")
        self._phase_i_spanning_tree()
        print(f"  Created {len(self.edges)} edges (spanning tree)")

        # Phase II: Greedy augmentation
        print("\n[Phase II] Greedy augmentation toward hub-and-spoke...")
        self._phase_ii_greedy_augmentation()
        print(f"  Total edges after Phase II: {len(self.edges)}")

        # Phase III: Local spokes (optional)
        if len(self.edges) < self.target_edges:
            print("\n[Phase III] Adding local spokes for non-hub nodes...")
            self._phase_iii_local_spokes()
            print(f"  Total edges after Phase III: {len(self.edges)}")

        print(f"\nConnection building complete: {len(self.edges)} edges created")
        self._print_statistics()

        # Verify graph correctness
        self.verify_graph()

    def _phase_i_spanning_tree(self) -> None:
        """
        Phase I: Build capacity-aware spanning tree.

        Orders nodes by capacity (descending) and connects each new node
        to the best previous node (maximizing preference score).
        """
        # Sort nodes by capacity (descending)
        sorted_nodes = sorted(self.nodes, key=lambda n: n.capacity_gbps, reverse=True)

        # Connect each node to the best parent among previously placed nodes
        for i in range(1, len(sorted_nodes)):
            current = sorted_nodes[i]

            # Find best parent (maximizes preference score)
            best_parent = None
            best_score = -1.0

            for j in range(i):
                candidate = sorted_nodes[j]
                score = self.calculate_preference_score(current, candidate)

                if score > best_score:
                    best_score = score
                    best_parent = candidate

            # Add edge with weight = eta * min(R_u, R_v)
            if best_parent:
                weight = self.eta * min(
                    self.residuals[current.name],
                    self.residuals[best_parent.name]
                )

                self._add_edge(current.name, best_parent.name, weight)

    def _phase_ii_greedy_augmentation(self) -> None:
        """
        Phase II: Greedy augmentation.

        Repeatedly selects the pair with highest preference score (among
        pairs with positive residuals) and adds an edge with score-scaled weight.
        """
        while len(self.edges) < self.target_edges:
            # Find best pair among all missing edges with positive residuals
            best_pair = None
            best_score = -1.0

            for i, node1 in enumerate(self.nodes):
                for j in range(i + 1, len(self.nodes)):
                    node2 = self.nodes[j]

                    # Skip if edge already exists
                    if self._edge_exists(node1.name, node2.name):
                        continue

                    # Skip if either node has no residual capacity
                    if self.residuals[node1.name] <= 0 or self.residuals[node2.name] <= 0:
                        continue

                    score = self.calculate_preference_score(node1, node2)

                    if score > best_score:
                        best_score = score
                        best_pair = (node1, node2)

            # If no feasible pair found, stop
            if best_pair is None:
                print(f"  No more feasible pairs (stopped at {len(self.edges)} edges)")
                break

            # Add edge with score-scaled weight
            node1, node2 = best_pair

            # Calculate normalized score
            s_hat = best_score / self.max_preference_score

            # Alpha function: α(S) = base + coefficient × S_normalized
            alpha = self.alpha_base_phase2 + self.alpha_coefficient_phase2 * s_hat

            # Weight = α(S_hat) * min(R_u, R_v)
            weight = alpha * min(
                self.residuals[node1.name],
                self.residuals[node2.name]
            )

            self._add_edge(node1.name, node2.name, weight)

    def _phase_iii_local_spokes(self) -> None:
        """
        Phase III: Local spokes for non-hub nodes.

        Non-hub nodes (bottom 75% by capacity) get additional connections
        to their best higher-capacity neighbors.
        """
        # Identify non-hub nodes based on threshold percentile
        sorted_nodes = sorted(self.nodes, key=lambda n: n.capacity_gbps, reverse=True)
        threshold_idx = int(self.non_hub_threshold * len(sorted_nodes))
        non_hub_nodes = sorted_nodes[threshold_idx:]

        for node in non_hub_nodes:
            # Skip if target reached
            if len(self.edges) >= self.target_edges:
                break

            # Skip if node has no residual
            if self.residuals[node.name] <= 0:
                continue

            # Find best higher-capacity neighbors not yet connected
            candidates = []
            for other in self.nodes:
                if other.capacity_gbps <= node.capacity_gbps:
                    continue
                if self._edge_exists(node.name, other.name):
                    continue
                if self.residuals[other.name] <= 0:
                    continue

                score = self.calculate_preference_score(node, other)
                candidates.append((score, other))

            # Sort by score and take top k
            candidates.sort(reverse=True, key=lambda x: x[0])

            for score, other in candidates[:self.spokes_per_node]:
                if len(self.edges) >= self.target_edges:
                    break

                # Add edge with scaled weight
                s_hat = score / self.max_preference_score
                alpha = self.alpha_base_phase3 + self.alpha_coefficient_phase3 * s_hat
                weight = alpha * min(
                    self.residuals[node.name],
                    self.residuals[other.name]
                )

                self._add_edge(node.name, other.name, weight)

    def _add_edge(self, node1_name: str, node2_name: str, weight: float) -> None:
        """
        Add an edge and update residual capacities.

        Args:
            node1_name: Name of first node
            node2_name: Name of second node
            weight: Edge weight
        """
        # Store edge (always store in sorted order for consistency)
        edge_key = tuple(sorted([node1_name, node2_name]))

        self.edges.append({
            'source': node1_name,
            'target': node2_name,
            'weight': weight
        })

        self.adjacency[edge_key] = weight

        # Update residuals
        self.residuals[node1_name] -= weight
        self.residuals[node2_name] -= weight

    def _edge_exists(self, node1_name: str, node2_name: str) -> bool:
        """Check if edge already exists."""
        edge_key = tuple(sorted([node1_name, node2_name]))
        return edge_key in self.adjacency

    def _print_statistics(self) -> None:
        """Print summary statistics about the generated graph."""
        if not self.edges:
            return

        weights = [e['weight'] for e in self.edges]
        total_capacity_used = {}

        for edge in self.edges:
            for node_name in [edge['source'], edge['target']]:
                if node_name not in total_capacity_used:
                    total_capacity_used[node_name] = 0.0
                total_capacity_used[node_name] += edge['weight']

        print("\nGraph Statistics:")
        print(f"  Total edges: {len(self.edges)}")
        print(f"  Edge weight range: {min(weights):.2f} - {max(weights):.2f} Gbps")
        print(f"  Average edge weight: {np.mean(weights):.2f} Gbps")
        print(f"  Total capacity allocated: {sum(weights) * 2:.2f} Gbps")

        # Node degree distribution
        degrees = {}
        for edge in self.edges:
            for node in [edge['source'], edge['target']]:
                degrees[node] = degrees.get(node, 0) + 1

        degree_values = list(degrees.values())
        print(f"  Node degree range: {min(degree_values)} - {max(degree_values)}")
        print(f"  Average node degree: {np.mean(degree_values):.2f}")

    def verify_graph(self) -> Dict:
        """
        Verify graph correctness based on connectedness and capacity constraints.

        Returns:
            Dictionary containing verification results with keys:
                - 'connected': bool
                - 'capacity_valid': bool
                - 'all_valid': bool (True if both checks pass)
                - 'report': dict with detailed statistics

        Raises:
            ValueError: If graph verification fails
        """
        if not self.nodes or not self.edges:
            raise ValueError("Cannot verify empty graph")

        print("\n[VERIFICATION] Checking graph correctness...")

        verification_result = {
            'connected': False,
            'capacity_valid': False,
            'all_valid': False,
            'report': {}
        }

        # ===== 1. CHECK CONNECTEDNESS (BFS) =====
        # Build adjacency list for BFS
        adj_list = {node.name: [] for node in self.nodes}
        for edge in self.edges:
            adj_list[edge['source']].append(edge['target'])
            adj_list[edge['target']].append(edge['source'])

        # BFS from first node
        start_node = self.nodes[0].name
        visited = set()
        queue = [start_node]
        visited.add(start_node)

        while queue:
            current = queue.pop(0)
            for neighbor in adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Check if all nodes were reached
        all_node_names = {node.name for node in self.nodes}
        disconnected_nodes = all_node_names - visited
        is_connected = len(disconnected_nodes) == 0

        verification_result['connected'] = is_connected
        verification_result['report']['total_nodes'] = len(self.nodes)
        verification_result['report']['reachable_nodes'] = len(visited)
        verification_result['report']['disconnected_nodes'] = list(disconnected_nodes)

        if is_connected:
            print(f"[VERIFICATION] Connectedness: PASSED (all {len(self.nodes)} nodes reachable)")
        else:
            print(f"[VERIFICATION] Connectedness: FAILED")
            print(f"  - Reachable nodes: {len(visited)}/{len(self.nodes)}")
            print(f"  - Disconnected nodes: {disconnected_nodes}")

        # ===== 2. CHECK CAPACITY CONSTRAINTS =====
        # Calculate total capacity used per node
        capacity_used = {node.name: 0.0 for node in self.nodes}
        for edge in self.edges:
            capacity_used[edge['source']] += edge['weight']
            capacity_used[edge['target']] += edge['weight']

        # Check for violations
        violations = []
        node_capacities = {node.name: node.capacity_gbps for node in self.nodes}
        remaining_capacities = {}

        for node in self.nodes:
            used = capacity_used[node.name]
            capacity = node.capacity_gbps
            remaining = capacity - used
            remaining_capacities[node.name] = remaining

            # Allow small floating point tolerance
            if remaining < -self.capacity_tolerance:
                violations.append({
                    'node': node.name,
                    'capacity': capacity,
                    'used': used,
                    'overage': -remaining
                })

        is_capacity_valid = len(violations) == 0

        verification_result['capacity_valid'] = is_capacity_valid
        verification_result['report']['capacity_violations'] = violations
        verification_result['report']['num_violations'] = len(violations)

        if remaining_capacities:
            min_remaining = min(remaining_capacities.values())
            max_remaining = max(remaining_capacities.values())
            min_node = min(remaining_capacities, key=remaining_capacities.get)
            max_node = max(remaining_capacities, key=remaining_capacities.get)

            verification_result['report']['min_remaining_capacity'] = min_remaining
            verification_result['report']['max_remaining_capacity'] = max_remaining
            verification_result['report']['min_remaining_node'] = min_node
            verification_result['report']['max_remaining_node'] = max_node

        if is_capacity_valid:
            print(f"[VERIFICATION] Capacity Constraints: PASSED")
            print(f"  - Node capacity violations: 0")
            print(f"  - Min remaining capacity: {min_remaining:.2f} Gbps (node: {min_node})")
            print(f"  - Max remaining capacity: {max_remaining:.2f} Gbps (node: {max_node})")
        else:
            print(f"[VERIFICATION] Capacity Constraints: FAILED")
            print(f"  - Node capacity violations: {len(violations)}")
            for v in violations[:5]:  # Show first 5 violations
                print(f"    • {v['node']}: capacity={v['capacity']:.2f} Gbps, "
                      f"used={v['used']:.2f} Gbps, overage={v['overage']:.2f} Gbps")
            if len(violations) > 5:
                print(f"    ... and {len(violations) - 5} more violations")

        # ===== 3. FINAL VERDICT =====
        all_valid = is_connected and is_capacity_valid
        verification_result['all_valid'] = all_valid

        if all_valid:
            print(f"[VERIFICATION] Graph is VALID")
        else:
            error_msg = "Graph verification FAILED:\n"
            if not is_connected:
                error_msg += f"  - Graph is not connected ({len(disconnected_nodes)} disconnected nodes)\n"
            if not is_capacity_valid:
                error_msg += f"  - Capacity constraints violated ({len(violations)} nodes exceed capacity)\n"
            print(f"[VERIFICATION] Graph is INVALID")
            raise ValueError(error_msg.strip())

        return verification_result

    def get_edges_dataframe(self) -> pd.DataFrame:
        """
        Get edges as a pandas DataFrame.

        Returns:
            DataFrame with columns: source, target, weight
        """
        return pd.DataFrame(self.edges)

    def export_adjacency_matrix(self, output_path: str) -> None:
        """
        Export adjacency matrix to CSV file.

        Args:
            output_path: Path to output CSV file
        """
        # Create node name list (sorted for consistency)
        node_names = sorted([node.name for node in self.nodes])
        n = len(node_names)

        # Create adjacency matrix
        matrix = np.zeros((n, n))

        for i, name1 in enumerate(node_names):
            for j, name2 in enumerate(node_names):
                if i == j:
                    continue

                edge_key = tuple(sorted([name1, name2]))
                if edge_key in self.adjacency:
                    matrix[i, j] = self.adjacency[edge_key]

        # Create DataFrame with node names as index and columns
        df = pd.DataFrame(matrix, index=node_names, columns=node_names)

        # Export to CSV
        df.to_csv(output_path)
        print(f"\nAdjacency matrix exported to: {output_path}")
