"""
Export SQLite database to JSON format.
Maintains backward compatibility with file-based tools.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.database_manager import NetworkDatabase


def export_services_to_json(db: NetworkDatabase, output_path: str) -> None:
    """
    Export services from database to JSON file.

    Includes full registries for nodes and edges.

    Args:
        db: NetworkDatabase instance
        output_path: Path to output JSON file
    """
    print(f"Exporting services to {output_path}...")

    # Get all data
    all_nodes = db.get_all_nodes()
    all_edges = db.get_all_edges()
    all_services = db.get_all_services()

    # Build node registry
    node_registry = {}
    for node in all_nodes:
        node_registry[node['uuid']] = {
            "name": node['name'],
            "latitude": node['latitude'],
            "longitude": node['longitude'],
            "vendor": node['vendor'],
            "capacity_gbps": node['capacity_gbps']
        }

    # Build edge registry
    edge_registry = {}
    for edge in all_edges:
        edge_registry[edge['uuid']] = {
            "node_1_uuid": edge['node1_uuid'],
            "node_2_uuid": edge['node2_uuid'],
            "capacity_gbps": edge['capacity_gbps']
        }

    # Build services list
    services_list = []
    for svc in all_services:
        services_list.append({
            "service_uuid": svc['uuid'],
            "name": svc['name'],
            "source_node_uuid": svc['source_node_uuid'],
            "destination_node_uuid": svc['destination_node_uuid'],
            "path_node_uuids": svc['path_node_uuids'],
            "path_edge_uuids": svc['path_edge_uuids'],
            "demand_gbps": svc['demand_gbps'],
            "hop_count": svc['hop_count'],
            "total_distance_km": round(svc['total_distance_km'], 2),
            "timestamp": svc['service_timestamp']
        })

    # Build metadata
    stage_a_count = sum(1 for svc in all_services if svc['routing_stage'] == 'stage_a')
    stage_b_count = sum(1 for svc in all_services if svc['routing_stage'] == 'stage_b')

    metadata = {
        "total_services": len(all_services),
        "demand_per_service_gbps": all_services[0]['demand_gbps'] if all_services else 0,
        "stage_a_services": stage_a_count,
        "stage_b_services": stage_b_count,
        "database_export": True,
        "export_timestamp": None  # Will be set below
    }

    # Add current timestamp
    from datetime import datetime
    metadata["export_timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Combine all data
    output = {
        "metadata": metadata,
        "registries": {
            "nodes": node_registry,
            "edges": edge_registry
        },
        "services": services_list
    }

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Exported {len(all_services)} services to {output_path}")
    print(f"  Node registry: {len(node_registry)} nodes")
    print(f"  Edge registry: {len(edge_registry)} edges")


def main():
    """Main export function."""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "data" / "network.db"
    output_path = script_dir.parent / "data" / "services_export.json"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run import_existing_data.py first to create the database.")
        sys.exit(1)

    print("=" * 70)
    print("DATABASE EXPORT: SQLite → JSON")
    print("=" * 70)

    db = NetworkDatabase(str(db_path))
    export_services_to_json(db, str(output_path))
    db.close()

    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
