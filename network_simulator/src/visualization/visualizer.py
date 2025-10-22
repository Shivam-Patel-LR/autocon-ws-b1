"""
Visualization module for the network simulator.
Creates geographic visualizations of network elements using matplotlib and geopandas.
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point
import geodatasets


class NetworkVisualizer:
    """
    Handles visualization of network elements on geographic maps.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the NetworkVisualizer.

        Args:
            output_dir: Directory to save output visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def create_network_map(
        self,
        df_elements: pd.DataFrame,
        output_filename: str = "network_map.png",
        figsize: tuple = (16, 12),
        dpi: int = 150
    ) -> str:
        """
        Create a map visualization of network elements.

        Args:
            df_elements: DataFrame containing network element data
            output_filename: Name of the output file
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch

        Returns:
            Path to the saved figure
        """
        # Create GeoDataFrame from network elements
        geometry = [Point(xy) for xy in zip(df_elements['long'], df_elements['lat'])]
        gdf_elements = gpd.GeoDataFrame(df_elements, geometry=geometry, crs="EPSG:4326")

        # Load US states data with actual state boundaries
        print("  Loading US states geographic data...")
        gdf_states = None

        # Try to get US state boundaries from Natural Earth (admin level 1 = states/provinces)
        try:
            # Use Natural Earth states/provinces boundaries
            states_url = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip'
            print("  Downloading US state boundaries from Census Bureau...")
            gdf_all_states = gpd.read_file(states_url)

            # Filter to continental eastern states
            eastern_state_codes = [
                'NY', 'PA', 'NJ', 'MA', 'CT', 'RI', 'NH', 'VT', 'ME', 'DE', 'MD',
                'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'AL', 'TN', 'KY', 'OH', 'IN',
                'MI', 'IL', 'WI', 'MS', 'LA'
            ]

            gdf_states = gdf_all_states[gdf_all_states['STUSPS'].isin(eastern_state_codes)]
            print(f"  Loaded {len(gdf_states)} US states")

        except Exception as e:
            print(f"  Note: Could not load Census Bureau data ({e}), trying alternative...")
            # Fall back to Natural Earth land masses
            try:
                states_path = geodatasets.get_path('naturalearth.land')
                gdf_states = gpd.read_file(states_path)
                gdf_states = gdf_states.cx[-100:-60, 20:50]
                print("  Using Natural Earth land boundaries")
            except:
                gdf_states = None
                print("  Warning: Could not load any geographic boundaries")

        # Create figure and axis
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Set background color to ocean blue
        ax.set_facecolor('#cfe2f3')

        # Plot states if available
        if gdf_states is not None:
            print("  Rendering state boundaries...")
            gdf_states.plot(
                ax=ax,
                color='#f8f8f0',  # Off-white/cream for land
                edgecolor='#333333',  # Dark gray for state borders
                linewidth=1.8,
                alpha=1.0,
                zorder=1
            )

        # Set map bounds to eastern US
        ax.set_xlim(-92, -65)  # From west of Mississippi to Atlantic coast
        ax.set_ylim(24, 48)    # From southern Florida to Canadian border

        # Add subtle reference grid
        print("  Adding reference grid...")
        for lon in range(-90, -65, 5):
            ax.axvline(x=lon, color='gray', linestyle=':', alpha=0.15, linewidth=0.6)
        for lat in range(25, 48, 5):
            ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.15, linewidth=0.6)

        # Plot network elements using geopandas plot method
        print("  Plotting network elements...")
        gdf_elements.plot(
            ax=ax,
            column='capacity_gbps',
            cmap='Greens',
            markersize=200,
            alpha=0.85,
            edgecolor='black',
            linewidth=1.2,
            legend=True,
            legend_kwds={
                'label': 'Capacity (Gbps)',
                'orientation': 'vertical',
                'shrink': 0.8,
                'pad': 0.02
            },
            zorder=5
        )

        # Add title and labels
        ax.set_title('Network Elements Distribution - Eastern United States', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Add statistics text box
        stats_text = (
            f"Total Elements: {len(df_elements)}\n"
            f"Total Capacity: {df_elements['capacity_gbps'].sum():,} Gbps\n"
            f"Avg Capacity: {df_elements['capacity_gbps'].mean():.0f} Gbps\n"
            f"Capacity Range: {df_elements['capacity_gbps'].min()}-{df_elements['capacity_gbps'].max()} Gbps"
        )
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )

        # Adjust layout
        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        print(f"Network map saved to: {output_path}")
        return str(output_path)

    def create_capacity_distribution(
        self,
        df_elements: pd.DataFrame,
        df_edges: pd.DataFrame = None,
        output_filename: str = "capacity_distribution.png",
        figsize: tuple = (12, 6),
        dpi: int = 150
    ) -> str:
        """
        Create histograms showing capacity distributions for nodes and connections.

        Args:
            df_elements: DataFrame containing network element data
            df_edges: DataFrame containing edge data (source, target, weight), optional
            output_filename: Name of the output file
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch

        Returns:
            Path to the saved figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Histogram of node capacities
        ax1.hist(df_elements['capacity_gbps'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax1.set_xlabel('Node Capacity (Gbps)', fontsize=12)
        ax1.set_ylabel('Number of Network Elements', fontsize=12)
        ax1.set_title('Node Capacity Distribution', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')

        # Histogram of connection weights
        if df_edges is not None and not df_edges.empty:
            ax2.hist(df_edges['weight'], bins=30, color='coral', edgecolor='black', alpha=0.7)
            ax2.set_xlabel('Connection Weight (Gbps)', fontsize=12)
            ax2.set_ylabel('Number of Connections', fontsize=12)
            ax2.set_title('Connection Weight Distribution', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, linestyle='--')

            # Add statistics text
            stats_text = (
                f"Total: {len(df_edges)}\n"
                f"Mean: {df_edges['weight'].mean():.1f} Gbps\n"
                f"Median: {df_edges['weight'].median():.1f} Gbps\n"
                f"Range: {df_edges['weight'].min():.2f}-{df_edges['weight'].max():.1f}"
            )
            ax2.text(
                0.98, 0.97, stats_text,
                transform=ax2.transAxes,
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )
        else:
            ax2.text(0.5, 0.5, 'No connection data available',
                    transform=ax2.transAxes,
                    fontsize=14, ha='center', va='center',
                    color='gray')
            ax2.set_title('Connection Weight Distribution', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        print(f"Capacity distribution saved to: {output_path}")
        return str(output_path)

    def create_connection_map(
        self,
        df_elements: pd.DataFrame,
        df_edges: pd.DataFrame,
        output_filename: str = "network_connections_map.png",
        figsize: tuple = (16, 12),
        dpi: int = 150
    ) -> str:
        """
        Create a map visualization showing network connections between elements.

        Args:
            df_elements: DataFrame containing network element data
            df_edges: DataFrame containing edge data (source, target, weight)
            output_filename: Name of the output file
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch

        Returns:
            Path to the saved figure
        """
        print("\n  Creating connection map visualization...")

        # Create GeoDataFrame from network elements
        geometry = [Point(xy) for xy in zip(df_elements['long'], df_elements['lat'])]
        gdf_elements = gpd.GeoDataFrame(df_elements, geometry=geometry, crs="EPSG:4326")

        # Create a mapping from node name to coordinates
        node_coords = {}
        for _, row in df_elements.iterrows():
            node_coords[row['name']] = (row['long'], row['lat'])

        # Load US states data
        print("  Loading US states geographic data...")
        gdf_states = None

        try:
            states_url = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip'
            print("  Downloading US state boundaries...")
            gdf_all_states = gpd.read_file(states_url)

            eastern_state_codes = [
                'NY', 'PA', 'NJ', 'MA', 'CT', 'RI', 'NH', 'VT', 'ME', 'DE', 'MD',
                'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'AL', 'TN', 'KY', 'OH', 'IN',
                'MI', 'IL', 'WI', 'MS', 'LA'
            ]

            gdf_states = gdf_all_states[gdf_all_states['STUSPS'].isin(eastern_state_codes)]
            print(f"  Loaded {len(gdf_states)} US states")

        except Exception as e:
            print(f"  Note: Could not load Census Bureau data ({e}), trying alternative...")
            try:
                states_path = geodatasets.get_path('naturalearth.land')
                gdf_states = gpd.read_file(states_path)
                gdf_states = gdf_states.cx[-100:-60, 20:50]
                print("  Using Natural Earth land boundaries")
            except:
                gdf_states = None
                print("  Warning: Could not load any geographic boundaries")

        # Create figure and axis
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Set background color to ocean blue
        ax.set_facecolor('#cfe2f3')

        # Plot states if available
        if gdf_states is not None:
            print("  Rendering state boundaries...")
            gdf_states.plot(
                ax=ax,
                color='#f8f8f0',
                edgecolor='#333333',
                linewidth=1.8,
                alpha=1.0,
                zorder=1
            )

        # Set map bounds to eastern US
        ax.set_xlim(-92, -65)
        ax.set_ylim(24, 48)

        # Add subtle reference grid
        for lon in range(-90, -65, 5):
            ax.axvline(x=lon, color='gray', linestyle=':', alpha=0.15, linewidth=0.6)
        for lat in range(25, 48, 5):
            ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.15, linewidth=0.6)

        # Plot edges (connections) with cool colormap (cyan to magenta) based on weight
        print("  Plotting network connections...")

        if not df_edges.empty:
            # Normalize edge weights for color mapping (log scale)
            min_weight = df_edges['weight'].min()
            max_weight = df_edges['weight'].max()

            # Create a colormap for cool (cyan to magenta)
            cmap = plt.cm.cool
            norm = mcolors.LogNorm(vmin=min_weight, vmax=max_weight)

            # Draw each edge
            for _, edge in df_edges.iterrows():
                source = edge['source']
                target = edge['target']
                weight = edge['weight']

                if source in node_coords and target in node_coords:
                    x_coords = [node_coords[source][0], node_coords[target][0]]
                    y_coords = [node_coords[source][1], node_coords[target][1]]

                    # Color based on weight
                    color = cmap(norm(weight))

                    ax.plot(
                        x_coords,
                        y_coords,
                        color=color,
                        linewidth=0.8,
                        alpha=0.6,
                        zorder=2
                    )

            # Add colorbar for edge weights
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02, shrink=0.8)
            cbar.set_label('Connection Weight (Gbps, log scale)', fontsize=11, fontweight='bold')

        # Plot network elements (nodes) on top with log scale
        print("  Plotting network nodes...")
        # Create log normalizer for node capacities
        min_capacity = df_elements['capacity_gbps'].min()
        max_capacity = df_elements['capacity_gbps'].max()
        capacity_norm = mcolors.LogNorm(vmin=min_capacity, vmax=max_capacity)

        gdf_elements.plot(
            ax=ax,
            column='capacity_gbps',
            cmap='Greens',
            norm=capacity_norm,
            markersize=150,
            alpha=0.95,
            edgecolor='black',
            linewidth=1.5,
            legend=True,
            legend_kwds={
                'label': 'Node Capacity (Gbps, log scale)',
                'orientation': 'vertical',
                'shrink': 0.8,
                'pad': 0.12
            },
            zorder=5
        )

        # Add title and labels
        ax.set_title(
            'Network Connections - Eastern United States',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Add statistics text box
        num_edges = len(df_edges)
        avg_weight = df_edges['weight'].mean() if not df_edges.empty else 0
        total_capacity_allocated = df_edges['weight'].sum() * 2 if not df_edges.empty else 0

        stats_text = (
            f"Network Statistics:\n"
            f"  Nodes: {len(df_elements)}\n"
            f"  Connections: {num_edges}\n"
            f"  Avg Weight: {avg_weight:.1f} Gbps\n"
            f"  Total Allocated: {total_capacity_allocated:,.0f} Gbps"
        )
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85),
            zorder=10
        )

        # Adjust layout
        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        print(f"Connection map saved to: {output_path}")
        return str(output_path)
