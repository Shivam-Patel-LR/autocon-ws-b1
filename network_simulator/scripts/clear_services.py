"""
Clear services from database for testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.database_manager import NetworkDatabase


def main():
    db = NetworkDatabase("data/network.db")

    # Clear services
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM services")
    cursor.execute("DELETE FROM service_path_nodes")
    cursor.execute("DELETE FROM service_path_edges")
    cursor.execute("UPDATE capacity_utilization SET total_demand_gbps = 0, service_count = 0")
    db.conn.commit()
    cursor.close()

    stats = db.get_stats()
    print(f"Services cleared. Database now has:")
    print(f"  Nodes: {stats['nodes']}")
    print(f"  Edges: {stats['edges']}")
    print(f"  Services: {stats['services']}")

    db.close()


if __name__ == "__main__":
    main()
