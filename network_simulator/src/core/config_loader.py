"""
Configuration loader for network simulator.
Loads and validates config.json with fallback to default values.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class NetworkConfig:
    """
    Configuration container for network simulator parameters.
    Loads from config.json and provides easy access to all parameters.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from JSON file.

        Args:
            config_path: Path to config.json file. If None, looks in parent directory.
        """
        if config_path is None:
            # Default: look for config.json in project root (two levels up from src/core/)
            config_path = Path(__file__).parent.parent.parent / "config.json"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file with fallback to defaults."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            print(f"Loaded configuration from: {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default values")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            print("Using default values")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config.json is missing."""
        return {
            "connection_algorithm": {
                "gamma": {"value": 1.5},
                "beta": {"value": 2.0},
                "eta": {"value": 0.4},
                "target_edges": {"value": 200},
                "noise_factor": {"value": 0.01},
                "random_seed": {"value": 42}
            },
            "alpha_functions": {
                "phase_ii": {
                    "alpha_base": {"value": 0.25},
                    "alpha_coefficient": {"value": 0.25}
                },
                "phase_iii": {
                    "alpha_base": {"value": 0.25},
                    "alpha_coefficient": {"value": 0.25}
                }
            },
            "graph_construction": {
                "min_distance_threshold": {"value": 0.001},
                "non_hub_threshold": {"value": 0.75},
                "spokes_per_node": {"value": 2},
                "capacity_tolerance": {"value": 1e-6}
            },
            "service_routing": {
                "demand_gbps": {"value": 5.0},
                "target_services": {"value": 100},
                "p_exponent": {"value": 1.5},
                "rho_exponent": {"value": 1.0},
                "noise_delta": {"value": 0.01},
                "random_seed": {"value": 42},
                "enable_stage_a": {"value": True}
            },
            "paths": {
                "data_dir": {"value": "data"},
                "output_dir": {"value": "output"}
            }
        }

    def _get_value(self, *path: str, default=None) -> Any:
        """
        Navigate nested config and extract value field.

        Args:
            *path: Path through nested dictionaries
            default: Default value if path not found

        Returns:
            The value at the specified path, or default if not found
        """
        obj = self.config
        for key in path:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return default

        # Extract 'value' field if it exists
        if isinstance(obj, dict) and 'value' in obj:
            return obj['value']
        return obj if obj is not None else default

    # Connection Algorithm Parameters
    @property
    def gamma(self) -> float:
        """Capacity importance exponent in preference score."""
        return self._get_value("connection_algorithm", "gamma", default=1.5)

    @property
    def beta(self) -> float:
        """Distance importance exponent in preference score."""
        return self._get_value("connection_algorithm", "beta", default=2.0)

    @property
    def eta(self) -> float:
        """Weight fraction for Phase I edges."""
        return self._get_value("connection_algorithm", "eta", default=0.4)

    @property
    def target_edges(self) -> int:
        """Target number of edges to create."""
        return self._get_value("connection_algorithm", "target_edges", default=200)

    @property
    def noise_factor(self) -> float:
        """Random noise factor for organic variation."""
        return self._get_value("connection_algorithm", "noise_factor", default=0.01)

    @property
    def random_seed(self) -> Optional[int]:
        """Random seed for reproducibility."""
        return self._get_value("connection_algorithm", "random_seed", default=42)

    # Alpha Function Parameters
    @property
    def alpha_base_phase2(self) -> float:
        """Base alpha value for Phase II."""
        return self._get_value("alpha_functions", "phase_ii", "alpha_base", default=0.25)

    @property
    def alpha_coefficient_phase2(self) -> float:
        """Alpha coefficient for Phase II."""
        return self._get_value("alpha_functions", "phase_ii", "alpha_coefficient", default=0.25)

    @property
    def alpha_base_phase3(self) -> float:
        """Base alpha value for Phase III."""
        return self._get_value("alpha_functions", "phase_iii", "alpha_base", default=0.25)

    @property
    def alpha_coefficient_phase3(self) -> float:
        """Alpha coefficient for Phase III."""
        return self._get_value("alpha_functions", "phase_iii", "alpha_coefficient", default=0.25)

    # Graph Construction Parameters
    @property
    def min_distance_threshold(self) -> float:
        """Minimum distance threshold to avoid division by zero."""
        return self._get_value("graph_construction", "min_distance_threshold", default=0.001)

    @property
    def non_hub_threshold(self) -> float:
        """Percentile threshold for non-hub nodes."""
        return self._get_value("graph_construction", "non_hub_threshold", default=0.75)

    @property
    def spokes_per_node(self) -> int:
        """Maximum additional connections for non-hub nodes."""
        return self._get_value("graph_construction", "spokes_per_node", default=2)

    @property
    def capacity_tolerance(self) -> float:
        """Floating-point tolerance for capacity validation."""
        return self._get_value("graph_construction", "capacity_tolerance", default=1e-6)

    # Service Routing Parameters
    @property
    def demand_gbps(self) -> float:
        """Fixed bandwidth demand per service in Gbps."""
        return self._get_value("service_routing", "demand_gbps", default=5.0)

    @property
    def target_services(self) -> int:
        """Target number of services to generate."""
        return self._get_value("service_routing", "target_services", default=100)

    @property
    def p_exponent(self) -> float:
        """Cost function exponent for Dijkstra routing."""
        return self._get_value("service_routing", "p_exponent", default=1.5)

    @property
    def rho_exponent(self) -> float:
        """Endpoint sampling weight exponent."""
        return self._get_value("service_routing", "rho_exponent", default=1.0)

    @property
    def noise_delta(self) -> float:
        """Uniform tie-breaking noise range."""
        return self._get_value("service_routing", "noise_delta", default=0.01)

    @property
    def service_random_seed(self) -> Optional[int]:
        """Random seed for service generation."""
        return self._get_value("service_routing", "random_seed", default=42)

    @property
    def enable_stage_a(self) -> bool:
        """Whether to enable Stage A edge cover routing."""
        return self._get_value("service_routing", "enable_stage_a", default=True)

    # Path Parameters
    @property
    def data_dir(self) -> str:
        """Directory containing input CSV files."""
        return self._get_value("paths", "data_dir", default="data")

    @property
    def output_dir(self) -> str:
        """Directory for generated visualizations."""
        return self._get_value("paths", "output_dir", default="output")

    def print_summary(self):
        """Print a summary of loaded configuration."""
        print("\n" + "=" * 60)
        print("Network Simulator Configuration")
        print("=" * 60)
        print("\nConnection Algorithm:")
        print(f"  γ (gamma):        {self.gamma}")
        print(f"  β (beta):         {self.beta}")
        print(f"  η (eta):          {self.eta}")
        print(f"  Target edges:     {self.target_edges}")
        print(f"  Noise factor:     {self.noise_factor}")
        print(f"  Random seed:      {self.random_seed}")

        print("\nAlpha Functions:")
        print(f"  Phase II:   α ∈ [{self.alpha_base_phase2:.2f}, {self.alpha_base_phase2 + self.alpha_coefficient_phase2:.2f}]")
        print(f"  Phase III:  α ∈ [{self.alpha_base_phase3:.2f}, {self.alpha_base_phase3 + self.alpha_coefficient_phase3:.2f}]")

        print("\nGraph Construction:")
        print(f"  Min distance:     {self.min_distance_threshold}")
        print(f"  Non-hub cutoff:   {self.non_hub_threshold * 100:.0f}th percentile")
        print(f"  Spokes per node:  {self.spokes_per_node}")

        print("\nPaths:")
        print(f"  Data directory:   {self.data_dir}")
        print(f"  Output directory: {self.output_dir}")
        print("=" * 60 + "\n")


# Module-level function for convenience
def load_config(config_path: Optional[str] = None) -> NetworkConfig:
    """
    Load network configuration from JSON file.

    Args:
        config_path: Optional path to config.json. If None, uses default location.

    Returns:
        NetworkConfig object with all parameters loaded
    """
    return NetworkConfig(config_path)


# For direct usage: from config_loader import config
_default_config = None


def get_config() -> NetworkConfig:
    """Get the default configuration instance (singleton pattern)."""
    global _default_config
    if _default_config is None:
        _default_config = load_config()
    return _default_config
