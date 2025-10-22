"""
Network Simulator main class.
Manages network elements and provides functionality for network simulation.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from core.network_element import NetworkElement
from core.connection_builder import ConnectionBuilder
from utilities.uuid_registry import NodeRegistry


class NetworkSimulator:
    """
    Main simulator class that manages network elements and connections.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the NetworkSimulator.

        Args:
            data_dir: Directory containing network data files
        """
        self.data_dir = Path(data_dir)
        self.network_elements: Dict[str, NetworkElement] = {}
        self.df_elements = None
        self.connection_builder: Optional[ConnectionBuilder] = None
        self.node_registry = NodeRegistry()

    def load_network_elements(self, filename: str = "network_elements.csv") -> None:
        """
        Load network elements from CSV file and register with UUID registry.

        Args:
            filename: Name of the CSV file containing network elements
        """
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Network elements file not found: {filepath}")

        # Load CSV into pandas DataFrame
        self.df_elements = pd.read_csv(filepath)

        # Create NetworkElement objects and register with UUID registry
        for _, row in self.df_elements.iterrows():
            # Register node and get UUID
            node_uuid = self.node_registry.register_node(
                name=row['name'],
                lat=row['lat'],
                long=row['long'],
                vendor=row['vendor'],
                capacity_gbps=row['capacity_gbps']
            )

            # Create NetworkElement with UUID
            ne = NetworkElement(
                name=row['name'],
                lat=row['lat'],
                long=row['long'],
                vendor=row['vendor'],
                capacity_gbps=row['capacity_gbps'],
                node_uuid=node_uuid
            )
            self.network_elements[ne.name] = ne

        print(f"Loaded {len(self.network_elements)} network elements with UUIDs")

    def get_network_element(self, name: str) -> NetworkElement:
        """
        Get a network element by name.

        Args:
            name: Name of the network element

        Returns:
            NetworkElement object

        Raises:
            KeyError: If network element not found
        """
        return self.network_elements[name]

    def get_all_elements(self) -> List[NetworkElement]:
        """
        Get all network elements.

        Returns:
            List of all NetworkElement objects
        """
        return list(self.network_elements.values())

    def get_elements_dataframe(self) -> pd.DataFrame:
        """
        Get network elements as a pandas DataFrame.

        Returns:
            DataFrame containing network element data
        """
        return self.df_elements

    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics about the network.

        Returns:
            Dictionary containing network statistics
        """
        if self.df_elements is None:
            return {}

        stats = {
            'total_elements': len(self.network_elements),
            'total_capacity_gbps': self.df_elements['capacity_gbps'].sum(),
            'avg_capacity_gbps': self.df_elements['capacity_gbps'].mean(),
            'max_capacity_gbps': self.df_elements['capacity_gbps'].max(),
            'min_capacity_gbps': self.df_elements['capacity_gbps'].min(),
            'unique_vendors': self.df_elements['vendor'].nunique()
        }

        # Add connection statistics if connections have been built
        if self.connection_builder is not None:
            edges = self.connection_builder.edges
            if edges:
                weights = [e['weight'] for e in edges]
                stats['total_edges'] = len(edges)
                stats['avg_edge_weight_gbps'] = sum(weights) / len(weights)
                stats['total_capacity_allocated_gbps'] = sum(weights) * 2

        return stats

    def build_connections(
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
    ) -> None:
        """
        Build node-to-node connections using the three-phase algorithm.

        Args:
            gamma: Capacity importance in preference score (typical: 1-2)
            beta: Distance importance in preference score (typical: 1-3)
            eta: Weight fraction for Phase I edges (must be in (0, 0.5])
            target_edges: Target number of edges to create (200-300)
            noise_factor: Small random noise for organic variation
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
        if not self.network_elements:
            raise ValueError("No network elements loaded. Call load_network_elements() first.")

        # Initialize connection builder with all parameters
        self.connection_builder = ConnectionBuilder(
            gamma=gamma,
            beta=beta,
            eta=eta,
            target_edges=target_edges,
            noise_factor=noise_factor,
            random_seed=random_seed,
            alpha_base_phase2=alpha_base_phase2,
            alpha_coefficient_phase2=alpha_coefficient_phase2,
            alpha_base_phase3=alpha_base_phase3,
            alpha_coefficient_phase3=alpha_coefficient_phase3,
            min_distance_threshold=min_distance_threshold,
            non_hub_threshold=non_hub_threshold,
            spokes_per_node=spokes_per_node,
            capacity_tolerance=capacity_tolerance
        )

        # Build connections
        elements_list = self.get_all_elements()
        self.connection_builder.build_connections(elements_list)

    def export_adjacency_matrix(self, filename: str = "adjacency_matrix.csv") -> str:
        """
        Export adjacency matrix to CSV file.

        Args:
            filename: Name of the output CSV file

        Returns:
            Path to the exported file
        """
        if self.connection_builder is None:
            raise ValueError("Connections not built. Call build_connections() first.")

        output_path = self.data_dir / filename
        self.connection_builder.export_adjacency_matrix(str(output_path))
        return str(output_path)

    def get_edges_dataframe(self) -> pd.DataFrame:
        """
        Get connection edges as a pandas DataFrame.

        Returns:
            DataFrame with columns: source, target, weight

        Raises:
            ValueError: If connections haven't been built yet
        """
        if self.connection_builder is None:
            raise ValueError("Connections not built. Call build_connections() first.")

        return self.connection_builder.get_edges_dataframe()
