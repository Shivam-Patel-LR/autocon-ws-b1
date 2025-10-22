"""
Main entry point for the network simulator.
Initializes the simulator, loads network elements, and generates visualizations.
"""

from core.network_simulator import NetworkSimulator
from visualization.visualizer import NetworkVisualizer
from core.config_loader import load_config


def main():
    """
    Main function to initialize and run the network simulator.
    """
    # Load configuration
    config = load_config()
    config.print_summary()

    print("=" * 60)
    print("Network Simulator - Initialization")
    print("=" * 60)

    # Initialize simulator with config
    simulator = NetworkSimulator(data_dir=config.data_dir)

    # Load network elements
    print("\nLoading network elements...")
    simulator.load_network_elements()

    # Display summary statistics
    print("\nNetwork Summary:")
    print("-" * 60)
    stats = simulator.get_summary_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"  {key.replace('_', ' ').title()}: {value}")

    # Initialize visualizer with config
    print("\n" + "=" * 60)
    print("Generating Visualizations")
    print("=" * 60)
    visualizer = NetworkVisualizer(output_dir=config.output_dir)

    # Create network map
    print("\nCreating network element map...")
    df = simulator.get_elements_dataframe()
    map_path = visualizer.create_network_map(df)

    # Build network connections with config parameters
    print("\n" + "=" * 60)
    print("Building Network Connections")
    print("=" * 60)
    simulator.build_connections(
        gamma=config.gamma,
        beta=config.beta,
        eta=config.eta,
        target_edges=config.target_edges,
        noise_factor=config.noise_factor,
        random_seed=config.random_seed,
        alpha_base_phase2=config.alpha_base_phase2,
        alpha_coefficient_phase2=config.alpha_coefficient_phase2,
        alpha_base_phase3=config.alpha_base_phase3,
        alpha_coefficient_phase3=config.alpha_coefficient_phase3,
        min_distance_threshold=config.min_distance_threshold,
        non_hub_threshold=config.non_hub_threshold,
        spokes_per_node=config.spokes_per_node,
        capacity_tolerance=config.capacity_tolerance,
    )

    # Note: Graph verification is automatically performed during build_connections()
    # and will raise an exception if the graph is invalid

    # Export adjacency matrix
    print("\nExporting adjacency matrix...")
    matrix_path = simulator.export_adjacency_matrix()

    # Create connection visualization
    print("\n" + "=" * 60)
    print("Generating Connection Visualization")
    print("=" * 60)
    df_edges = simulator.get_edges_dataframe()
    connection_map_path = visualizer.create_connection_map(df, df_edges)

    # Create capacity distribution charts (with connections)
    print("\nCreating capacity distribution charts...")
    dist_path = visualizer.create_capacity_distribution(df, df_edges)

    # Display final statistics
    print("\n" + "=" * 60)
    print("Network Summary (with Connections)")
    print("=" * 60)
    final_stats = simulator.get_summary_statistics()
    for key, value in final_stats.items():
        if isinstance(value, float):
            print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"  {key.replace('_', ' ').title()}: {value:,}")

    print("\n" + "=" * 60)
    print("Initialization Complete!")
    print("=" * 60)
    print(f"\nGenerated visualizations:")
    print(f"  - {map_path}")
    print(f"  - {dist_path}")
    print(f"  - {connection_map_path}")
    print(f"\nGenerated data files:")
    print(f"  - {matrix_path}")
    print("\nThe network simulator is now initialized and ready for use.")
    print("Review the PNG files in the output/ directory for manual inspection.")


if __name__ == "__main__":
    main()
