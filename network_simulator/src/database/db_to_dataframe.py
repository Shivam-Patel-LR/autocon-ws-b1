"""
Database to DataFrame conversion utilities.
Converts database records to pandas DataFrames for visualization and export.
"""

import pandas as pd
from typing import List, Dict
from database.database_manager import NetworkDatabase


def db_to_nodes_dataframe(db: NetworkDatabase) -> pd.DataFrame:
    """
    Convert nodes table to DataFrame compatible with visualizer.

    Args:
        db: NetworkDatabase instance

    Returns:
        DataFrame with columns: name, lat, long, vendor, capacity_gbps
    """
    nodes = db.get_all_nodes()

    data = [{
        'name': node['name'],
        'lat': node['latitude'],
        'long': node['longitude'],
        'vendor': node['vendor'],
        'capacity_gbps': node['capacity_gbps']
    } for node in nodes]

    return pd.DataFrame(data)


def db_to_edges_dataframe(db: NetworkDatabase) -> pd.DataFrame:
    """
    Convert edges table to DataFrame compatible with visualizer.

    Args:
        db: NetworkDatabase instance

    Returns:
        DataFrame with columns: source, target, weight
    """
    edges_data = []

    for edge in db.get_all_edges():
        # Get node names for source and target
        node1 = db.get_node_by_uuid(edge['node1_uuid'])
        node2 = db.get_node_by_uuid(edge['node2_uuid'])

        if node1 and node2:
            edges_data.append({
                'source': node1['name'],
                'target': node2['name'],
                'weight': edge['capacity_gbps']
            })

    return pd.DataFrame(edges_data)


def db_to_services_dataframe(db: NetworkDatabase) -> pd.DataFrame:
    """
    Convert services to DataFrame for analysis.

    Args:
        db: NetworkDatabase instance

    Returns:
        DataFrame with service information
    """
    services_data = []

    for service in db.get_all_services():
        # Get node names
        source_node = db.get_node_by_uuid(service['source_node_uuid'])
        dest_node = db.get_node_by_uuid(service['destination_node_uuid'])

        # Convert path UUIDs to names
        path_names = []
        for node_uuid in service['path_node_uuids']:
            node = db.get_node_by_uuid(node_uuid)
            if node:
                path_names.append(node['name'])

        if source_node and dest_node:
            services_data.append({
                'service_id': service['uuid'][:8] + '...',  # Shortened for display
                'name': service['name'],
                'source': source_node['name'],
                'destination': dest_node['name'],
                'path': ' → '.join(path_names),
                'demand_gbps': service['demand_gbps'],
                'hop_count': service['hop_count'],
                'distance_km': service['total_distance_km'],
                'timestamp': service['service_timestamp']
            })

    return pd.DataFrame(services_data)


def export_db_to_csv(db: NetworkDatabase, output_dir: str) -> Dict[str, str]:
    """
    Export database tables to CSV files.

    Args:
        db: NetworkDatabase instance
        output_dir: Directory to save CSV files

    Returns:
        Dictionary mapping table names to output file paths
    """
    from pathlib import Path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # Export nodes
    df_nodes = db_to_nodes_dataframe(db)
    nodes_path = output_path / "network_elements.csv"
    df_nodes.to_csv(nodes_path, index=False)
    outputs['nodes'] = str(nodes_path)

    # Export edges
    df_edges = db_to_edges_dataframe(db)
    edges_path = output_path / "network_edges.csv"
    df_edges.to_csv(edges_path, index=False)
    outputs['edges'] = str(edges_path)

    # Export services
    df_services = db_to_services_dataframe(db)
    services_path = output_path / "services_summary.csv"
    df_services.to_csv(services_path, index=False)
    outputs['services'] = str(services_path)

    return outputs
