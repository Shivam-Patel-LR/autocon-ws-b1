"""
Dummy network generator for testing and development.
Creates synthetic network elements when no CSV data is available.
"""

import random
import pandas as pd
from typing import List, Dict
from pathlib import Path


# Real cities in eastern US with accurate GPS coordinates
REAL_CITIES = {
    "New York-NY": {"lat": 40.7128, "lon": -74.0060},
    "Boston-MA": {"lat": 42.3601, "lon": -71.0589},
    "Philadelphia-PA": {"lat": 39.9526, "lon": -75.1652},
    "Pittsburgh-PA": {"lat": 40.4406, "lon": -79.9959},
    "Baltimore-MD": {"lat": 39.2904, "lon": -76.6122},
    "Washington-DC": {"lat": 38.9072, "lon": -77.0369},
    "Richmond-VA": {"lat": 37.5407, "lon": -77.4360},
    "Norfolk-VA": {"lat": 36.8508, "lon": -76.2859},
    "Raleigh-NC": {"lat": 35.7796, "lon": -78.6382},
    "Charlotte-NC": {"lat": 35.2271, "lon": -80.8431},
    "Atlanta-GA": {"lat": 33.7490, "lon": -84.3880},
    "Miami-FL": {"lat": 25.7617, "lon": -80.1918},
    "Orlando-FL": {"lat": 28.5383, "lon": -81.3792},
    "Jacksonville-FL": {"lat": 30.3322, "lon": -81.6557},
    "Tampa-FL": {"lat": 27.9506, "lon": -82.4572},
    "Charleston-SC": {"lat": 32.7765, "lon": -79.9311},
    "Columbia-SC": {"lat": 34.0007, "lon": -81.0348},
    "Nashville-TN": {"lat": 36.1627, "lon": -86.7816},
    "Memphis-TN": {"lat": 35.1495, "lon": -90.0490},
    "Knoxville-TN": {"lat": 35.9606, "lon": -83.9207},
    "Louisville-KY": {"lat": 38.2527, "lon": -85.7585},
    "Lexington-KY": {"lat": 38.0406, "lon": -84.5037},
    "Cincinnati-OH": {"lat": 39.1031, "lon": -84.5120},
    "Columbus-OH": {"lat": 39.9612, "lon": -82.9988},
    "Cleveland-OH": {"lat": 41.4993, "lon": -81.6944},
    "Akron-OH": {"lat": 41.0814, "lon": -81.5190},
    "Toledo-OH": {"lat": 41.6528, "lon": -83.5379},
    "Dayton-OH": {"lat": 39.7589, "lon": -84.1916},
    "Indianapolis-IN": {"lat": 39.7684, "lon": -86.1581},
    "Detroit-MI": {"lat": 42.3314, "lon": -83.0458},
    "Grand Rapids-MI": {"lat": 42.9634, "lon": -85.6681},
    "Lansing-MI": {"lat": 42.7325, "lon": -84.5555},
    "Chicago-IL": {"lat": 41.8781, "lon": -87.6298},
    "Springfield-IL": {"lat": 39.7817, "lon": -89.6501},
    "Buffalo-NY": {"lat": 42.8864, "lon": -78.8784},
    "Rochester-NY": {"lat": 43.1566, "lon": -77.6088},
    "Syracuse-NY": {"lat": 43.0481, "lon": -76.1474},
    "Albany-NY": {"lat": 42.6526, "lon": -73.7562},
    "Hartford-CT": {"lat": 41.7658, "lon": -72.6734},
    "New Haven-CT": {"lat": 41.3083, "lon": -72.9279},
    "Providence-RI": {"lat": 41.8240, "lon": -71.4128},
    "Portland-ME": {"lat": 43.6591, "lon": -70.2568},
    "Manchester-NH": {"lat": 42.9956, "lon": -71.4548},
    "Burlington-VT": {"lat": 44.4759, "lon": -73.2121},
    "Trenton-NJ": {"lat": 40.2171, "lon": -74.7429},
    "Newark-NJ": {"lat": 40.7357, "lon": -74.1724},
    "Wilmington-DE": {"lat": 39.7391, "lon": -75.5398},
    "Dover-DE": {"lat": 39.1582, "lon": -75.5244},
    "Harrisburg-PA": {"lat": 40.2732, "lon": -76.8867},
    "Scranton-PA": {"lat": 41.4090, "lon": -75.6624},
}


def generate_city_names(num_cities: int, seed: int = 42) -> List[str]:
    """
    Generate unique city names for network elements using real cities.

    Args:
        num_cities: Number of city names to generate
        seed: Random seed for reproducibility

    Returns:
        List of unique city names with accurate geographic locations
    """
    rng = random.Random(seed)

    # Get all available real city names
    available_cities = list(REAL_CITIES.keys())

    if num_cities > len(available_cities):
        raise ValueError(
            f"Requested {num_cities} cities but only {len(available_cities)} "
            f"real cities available in lookup table"
        )

    # Randomly sample without replacement
    selected_cities = rng.sample(available_cities, num_cities)

    return selected_cities


def generate_dummy_network(
    num_nodes: int = 48,
    seed: int = 42,
    hub_count: int = 10
) -> List[Dict]:
    """
    Generate dummy network elements for testing.

    Creates a realistic distribution of hub and regular nodes
    with random coordinates in eastern US region.

    Args:
        num_nodes: Total number of nodes to generate (default: 48)
        seed: Random seed for reproducibility
        hub_count: Number of high-capacity hub nodes (default: 10)

    Returns:
        List of dictionaries with node data
    """
    rng = random.Random(seed)

    # Generate city names
    cities = generate_city_names(num_nodes, seed)

    # Vendor distribution - Creative parodies of major networking vendors
    # Tonio (Cisco), Agave (Juniper), Toscana (Ciena), Cadenza (Arista), Suomi (Nokia)
    vendors = ['Tonio Networks', 'Agave Networks', 'Toscana Systems', 'Cadenza Networks', 'Suomi Networks']

    nodes = []

    for i, city in enumerate(cities):
        # Determine if this is a hub node (first hub_count nodes)
        is_hub = i < hub_count

        # Get actual geographic coordinates from lookup table
        city_data = REAL_CITIES[city]
        lat = city_data['lat']
        lon = city_data['lon']

        # Capacity distribution
        if is_hub:
            # Hub nodes: 3000-5000 Gbps
            capacity = rng.randint(3000, 5000)
        else:
            # Regular nodes: 400-2000 Gbps
            capacity = rng.randint(400, 2000)

        # Random vendor
        vendor = rng.choice(vendors)

        nodes.append({
            'name': city,
            'lat': lat,
            'long': lon,
            'vendor': vendor,
            'capacity_gbps': capacity
        })

    # Sort by capacity (descending) for better organization
    nodes.sort(key=lambda x: x['capacity_gbps'], reverse=True)

    return nodes


def save_nodes_to_csv(nodes: List[Dict], filepath: str) -> None:
    """
    Save node data to CSV file.

    Args:
        nodes: List of node dictionaries
        filepath: Output CSV file path
    """
    df = pd.DataFrame(nodes)

    # Ensure directory exists
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Saved {len(nodes)} nodes to {filepath}")


def load_nodes_from_csv(filepath: str) -> List[Dict]:
    """
    Load node data from CSV file.

    Args:
        filepath: CSV file path

    Returns:
        List of node dictionaries
    """
    df = pd.read_csv(filepath)
    return df.to_dict('records')


def generate_and_save_dummy_network(
    output_path: str,
    num_nodes: int = 48,
    seed: int = 42
) -> List[Dict]:
    """
    Generate dummy network and save to CSV.

    Args:
        output_path: Path to output CSV file
        num_nodes: Number of nodes to generate
        seed: Random seed

    Returns:
        List of generated node dictionaries
    """
    print(f"Generating dummy network with {num_nodes} nodes...")

    nodes = generate_dummy_network(num_nodes=num_nodes, seed=seed)

    save_nodes_to_csv(nodes, output_path)

    # Print summary
    total_capacity = sum(n['capacity_gbps'] for n in nodes)
    avg_capacity = total_capacity / len(nodes)
    vendor_counts = {}
    for node in nodes:
        vendor_counts[node['vendor']] = vendor_counts.get(node['vendor'], 0) + 1

    print(f"  Total nodes: {len(nodes)}")
    print(f"  Total capacity: {total_capacity:,} Gbps")
    print(f"  Average capacity: {avg_capacity:.0f} Gbps")
    print(f"  Vendors: {', '.join(f'{v}({c})' for v, c in vendor_counts.items())}")

    return nodes
