"""
Container initialization script.
Intelligently initializes based on database presence:
- If network.db exists: Load, verify, and visualize
- If network.db missing: Create new network and populate database
"""

import sys
import os
import uuid
import pandas as pd
from pathlib import Path

from core.config_loader import load_config
from database.database_manager import NetworkDatabase
from database.database_verifier_inline import DatabaseVerifier
from database.db_to_dataframe import db_to_nodes_dataframe, db_to_edges_dataframe
from utilities.dummy_network_generator import generate_and_save_dummy_network
from core.network_simulator import NetworkSimulator
from visualization.visualizer import NetworkVisualizer
from database.json_exporter import export_services_to_json


def check_database_exists(data_dir: str) -> bool:
    """Check if database file exists."""
    db_path = Path(data_dir) / "network.db"
    return db_path.exists()


def check_csv_exists(data_dir: str) -> bool:
    """Check if network_elements.csv exists."""
    csv_path = Path(data_dir) / "network_elements.csv"
    return csv_path.exists()


def load_and_verify_mode(config) -> None:
    """
    Load existing database, verify integrity, and generate visualizations.

    Args:
        config: NetworkConfig object
    """
    print("=" * 70)
    print("MODE: LOAD FROM EXISTING DATABASE")
    print("=" * 70)

    db_path = Path(config.data_dir) / "network.db"

    # Open database
    print(f"\nLoading database from {db_path}...")
    db = NetworkDatabase(str(db_path))

    # Display database statistics
    stats = db.get_stats()
    print(f"Database loaded successfully")
    print(f"  Nodes:    {stats['nodes']}")
    print(f"  Edges:    {stats['edges']}")
    print(f"  Services: {stats['services']}")

    # Run verification
    print("\nRunning verification checks...")
    verifier = DatabaseVerifier(db, verbose=True)
    passed = verifier.verify_all()

    if not passed:
        db.close()
        raise RuntimeError(
            f"Database verification FAILED with {len(verifier.errors)} error(s). "
            "Container initialization aborted."
        )

    # Convert database to DataFrames for visualization
    print("\nPreparing data for visualization...")
    df_nodes = db_to_nodes_dataframe(db)
    df_edges = db_to_edges_dataframe(db)
    print(f"  Converted {len(df_nodes)} nodes and {len(df_edges)} edges to DataFrames")

    # Generate visualizations
    print("\nGenerating visualizations...")
    visualizer = NetworkVisualizer(output_dir=config.output_dir)

    print("  Creating network map...")
    map_path = visualizer.create_network_map(df_nodes)

    print("  Creating connection map...")
    connection_map_path = visualizer.create_connection_map(df_nodes, df_edges)

    print("  Creating capacity distribution charts...")
    dist_path = visualizer.create_capacity_distribution(df_nodes, df_edges)

    # Export JSON
    print("\nExporting services to JSON...")
    export_path = Path(config.data_dir) / "services_export.json"
    export_services_to_json(db, str(export_path))

    # Display final summary
    print("\n" + "=" * 70)
    print("LOAD MODE COMPLETE")
    print("=" * 70)
    print(f"Database verified and loaded")
    print(f"Generated visualizations:")
    print(f"    - {map_path}")
    print(f"    - {connection_map_path}")
    print(f"    - {dist_path}")
    print(f"Exported: {export_path}")
    print("=" * 70)

    db.close()


def import_simulator_to_database(db: NetworkDatabase, simulator: NetworkSimulator) -> None:
    """
    Import NetworkSimulator data into database with UUIDs.

    Args:
        db: NetworkDatabase instance
        simulator: NetworkSimulator with loaded elements and connections
    """
    print("\nImporting network into database...")

    # Import nodes
    print("  Importing nodes...")
    name_to_uuid = {}

    with db.transaction():
        for name, element in simulator.network_elements.items():
            node_uuid = str(uuid.uuid4())
            name_to_uuid[name] = node_uuid

            db.insert_node(
                node_uuid=node_uuid,
                name=element.name,
                latitude=element.lat,
                longitude=element.long,
                vendor=element.vendor,
                capacity_gbps=element.capacity_gbps
            )

    print(f"    Imported {len(name_to_uuid)} nodes")

    # Import edges
    print("  Importing edges...")
    edge_count = 0

    if simulator.connection_builder:
        with db.transaction():
            for edge in simulator.connection_builder.edges:
                source_uuid = name_to_uuid[edge['source']]
                target_uuid = name_to_uuid[edge['target']]

                # Ensure canonical ordering
                if source_uuid > target_uuid:
                    source_uuid, target_uuid = target_uuid, source_uuid

                edge_uuid = str(uuid.uuid4())

                db.insert_edge(
                    edge_uuid=edge_uuid,
                    node1_uuid=source_uuid,
                    node2_uuid=target_uuid,
                    capacity_gbps=edge['weight']
                )
                edge_count += 1

    print(f"    Imported {edge_count} edges")


def create_new_network_mode(config) -> None:
    """
    Create new network from scratch, populate database.

    Args:
        config: NetworkConfig object
    """
    print("=" * 70)
    print("MODE: CREATE NEW NETWORK")
    print("=" * 70)

    db_path = Path(config.data_dir) / "network.db"

    # Step 1: Ensure network elements exist
    csv_path = Path(config.data_dir) / "network_elements.csv"

    if not csv_path.exists():
        print("\n🆕 No network_elements.csv found - generating dummy network...")
        generate_and_save_dummy_network(
            output_path=str(csv_path),
            num_nodes=48,  # Default network size
            seed=config.random_seed or 42
        )
    else:
        print(f"\nFound existing network_elements.csv")

    # Step 2: Initialize simulator and build connections
    print("\nBuilding network topology...")
    simulator = NetworkSimulator(data_dir=config.data_dir)

    simulator.load_network_elements()

    print("\nBuilding connections (3-phase algorithm)...")
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

    # Step 3: Create database and import
    print(f"\nCreating database at {db_path}...")
    db = NetworkDatabase(str(db_path))

    import_simulator_to_database(db, simulator)

    # Step 4: Generate services
    if os.getenv('GENERATE_SERVICES', 'true').lower() == 'true':
        print("\nGenerating services...")
        from services.generate_services_db import DatabaseServiceRouter

        router = DatabaseServiceRouter(
            db=db,
            demand=config.demand_gbps,
            p_exponent=config.p_exponent,
            rho_exponent=config.rho_exponent,
            noise_delta=config.noise_delta,
            random_seed=config.service_random_seed or 42,
            enable_stage_a=config.enable_stage_a
        )

        num_services = int(os.getenv('NUM_SERVICES', config.target_services))
        service_count = router.generate_services(target_count=num_services)
        print(f"    Generated {service_count} services")
    else:
        print("\nSkipping service generation (GENERATE_SERVICES=false)")

    # Step 5: Run verification
    print("\nRunning verification checks...")
    verifier = DatabaseVerifier(db, verbose=True)
    passed = verifier.verify_all()

    if not passed:
        db.close()
        raise RuntimeError(
            f"Verification FAILED with {len(verifier.errors)} error(s). "
            "Container initialization aborted."
        )

    # Step 6: Generate visualizations
    print("\nGenerating visualizations...")
    df_nodes = db_to_nodes_dataframe(db)
    df_edges = db_to_edges_dataframe(db)

    visualizer = NetworkVisualizer(output_dir=config.output_dir)

    print("  Creating network map...")
    map_path = visualizer.create_network_map(df_nodes)

    print("  Creating connection map...")
    connection_map_path = visualizer.create_connection_map(df_nodes, df_edges)

    print("  Creating capacity distribution charts...")
    dist_path = visualizer.create_capacity_distribution(df_nodes, df_edges)

    # Step 7: Export JSON
    print("\nExporting services to JSON...")
    export_path = Path(config.data_dir) / "services_export.json"
    export_services_to_json(db, str(export_path))

    # Display final summary
    final_stats = db.get_stats()
    print("\n" + "=" * 70)
    print("CREATE MODE COMPLETE")
    print("=" * 70)
    print(f"Database created: {db_path}")
    print(f"    Nodes: {final_stats['nodes']}, Edges: {final_stats['edges']}, Services: {final_stats['services']}")
    print(f"Generated visualizations:")
    print(f"    - {map_path}")
    print(f"    - {connection_map_path}")
    print(f"    - {dist_path}")
    print(f"Exported: {export_path}")
    print("=" * 70)

    db.close()


def main():
    """
    Main container initialization function.

    Decides between load mode and create mode based on database presence.
    """
    print("\n" + "=" * 70)
    print("NETWORK SIMULATOR - CONTAINER INITIALIZATION")
    print("=" * 70)

    # Check for force rebuild flag
    force_rebuild = os.getenv('FORCE_REBUILD', 'false').lower() == 'true'

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Check database existence
    db_path = Path(config.data_dir) / "network.db"
    db_exists = db_path.exists()

    if force_rebuild and db_exists:
        print("\nFORCE_REBUILD=true: Deleting existing database...")
        db_path.unlink()
        db_exists = False

    # Route to appropriate mode
    try:
        if db_exists:
            load_and_verify_mode(config)
        else:
            create_new_network_mode(config)

        print("\nContainer initialization complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\nContainer initialization FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
