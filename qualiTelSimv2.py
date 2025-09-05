import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import warnings
import os

# Suppress FastF1 warnings
warnings.filterwarnings('ignore')

class F1LaptimeSimulatorLayeredDominance:
    def __init__(self):
        # Create cache directory
        cache_dir = './cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"Created cache directory: {cache_dir}")
        
        fastf1.Cache.enable_cache(cache_dir)
        
    def load_data(self, year, round_num):
        """Load and process quali data"""
        print(f"Loading {year} Round {round_num} Qualifying data...")
        
        session = fastf1.get_session(year, round_num, 'Q')
        session.load()
        
        # Driver color mapping
        driver_colors = {
            'ALB': '#005aff', 'SAI': '#012564', 'LEC': '#dc0000', 'HAD': '#2b4562',
            'COL': '#ff117c', 'ALO': '#006f62', 'RUS': '#24ffff', 'OCO': "#6A6868",
            'STR': '#00413b', 'NOR': '#FF8700', 'HAM': '#ff2800', 'VER': '#23326A',
            'HUL': '#00e701', 'BEA': "#605e5e", 'PIA': '#FFD580', 'GAS': '#fe86bc',
            'LAW': "#50a8ac", 'ANT': "#a1fafa", 'TSU': '#356cac', 'BOR': '#008d01'
        }
        
        # Get top 3 drivers
        results = session.results.head(3)
        drivers_data = {}
        
        for i, (_, result) in enumerate(results.iterrows()):
            driver = result['Abbreviation']
            driver_laps = session.laps.pick_driver(driver)
            fastest_lap = driver_laps.pick_fastest()
            
            if fastest_lap is not None and not fastest_lap.empty:
                telemetry = fastest_lap.get_telemetry()
                if len(telemetry) > 0:
                    # Use actual driver color or fallback to default colors
                    color = driver_colors.get(driver, ['red', 'blue', 'green'][i])
                    
                    drivers_data[driver] = {
                        'telemetry': telemetry,
                        'color': color,
                        'team': result['TeamName'],
                        'laptime': fastest_lap['LapTime'],
                        'position': i + 1
                    }
        
        return drivers_data, session
    
    def optimize_track_layout(self, track_x, track_y):
        """Rotate and scale track"""
        
        # Center the track
        track_x_centered = track_x - np.mean(track_x)
        track_y_centered = track_y - np.mean(track_y)
        
        # Try different rotation angles to find best horizontal fit
        best_rotation = 0
        best_width_ratio = 0
        
        for angle_deg in range(0, 180, 10):
            angle_rad = np.radians(angle_deg)
            
            # Rotate track
            x_rot = track_x_centered * np.cos(angle_rad) - track_y_centered * np.sin(angle_rad)
            y_rot = track_x_centered * np.sin(angle_rad) + track_y_centered * np.cos(angle_rad)
            
            # Calculate dimensions
            rot_width = np.max(x_rot) - np.min(x_rot)
            rot_height = np.max(y_rot) - np.min(y_rot)
            
            # Calculate width to height ratio
            width_ratio = rot_width / (rot_height + 0.001)
            
            if width_ratio > best_width_ratio:
                best_width_ratio = width_ratio
                best_rotation = angle_deg
                track_x_rotated = x_rot
                track_y_rotated = y_rot
        
        
        return track_x_rotated, track_y_rotated
    
    def calculate_sector_dominance(self, drivers_data, num_sectors=100):
        """Calculate which driver is fastest in each sector"""
        
        min_length = min([len(data['telemetry']) for data in drivers_data.values()])
        sector_size = max(1, min_length // num_sectors)
        
        sector_colors = []
        sector_dominant_drivers = []
        
        for i in range(0, min_length, sector_size):
            sector_end = min(i + sector_size, min_length)
            sector_speeds = {}
            
            # Get average speed for each driver in this sector
            for driver, data in drivers_data.items():
                telemetry = data['telemetry']
                sector_tel = telemetry.iloc[i:sector_end]
                
                if len(sector_tel) > 0:
                    avg_speed = sector_tel['Speed'].mean()
                    sector_speeds[driver] = avg_speed
            
            # Find fastest driver in this sector
            if sector_speeds:
                fastest_driver = max(sector_speeds.keys(), key=lambda d: sector_speeds[d])
                fastest_color = drivers_data[fastest_driver]['color']
                
                points_in_sector = sector_end - i
                sector_colors.extend([fastest_color] * points_in_sector)
                sector_dominant_drivers.extend([fastest_driver] * points_in_sector)
            else:
                sector_colors.extend(['gray'] * (sector_end - i))
                sector_dominant_drivers.extend(['unknown'] * (sector_end - i))
        
        return sector_colors, sector_dominant_drivers
    
    def format_laptime(self, laptime_delta):
        """Format laptime delta to string"""
        if pd.isna(laptime_delta):
            return "No Time"
        
        total_seconds = laptime_delta.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        return f"{minutes}:{seconds:06.3f}"
    
    def setup_plots(self, drivers_data, session):
        """Setup plots"""
        
        # Create figure 
        fig, axes = plt.subplots(2, 2, figsize=(16, 13))
        fig.subplots_adjust(top=0.85, bottom=0.12, hspace=0.35)
        fig.suptitle(f"{session.event['EventName']} - Top 3 Q3 Comparison", fontsize=16, y=0.94)
        
        # Create horizontal lap time display
        sorted_drivers = sorted(drivers_data.items(), key=lambda x: x[1]['position'])
        laptime_parts = []
        
        for driver, data in sorted_drivers:
            position = data['position']
            laptime_str = self.format_laptime(data['laptime'])
            team = data['team']
            laptime_parts.append(f"P{position}: {driver} ({team}) - {laptime_str}")
        
        # Join horizontally
        laptime_text = "  |  ".join(laptime_parts)
        fig.text(0.5, 0.88, laptime_text, ha='center', fontsize=11, fontweight='bold')
        
        ax_track = axes[0, 0]
        ax_speed = axes[0, 1] 
        ax_throttle = axes[1, 0]
        ax_brake = axes[1, 1]
        
        # Analyze data ranges for scaling
        all_distances = []
        all_speeds = []
        all_throttles = []
        all_brakes = []
        
        for driver, data in drivers_data.items():
            tel = data['telemetry']
            all_distances.extend(tel['Distance'].values)
            all_speeds.extend(tel['Speed'].values)
            all_throttles.extend(tel['Throttle'].values) 
            all_brakes.extend(tel['Brake'].values)
        
        # Calculate ranges
        max_distance = max(all_distances)
        max_speed = max(all_speeds)
        max_throttle = max(all_throttles)
        max_brake = max(all_brakes)
        
        print(f"Data ranges - Distance: 0-{max_distance:.0f}m, Speed: 0-{max_speed:.0f}km/h")
        print(f"Throttle: 0-{max_throttle:.0f}%, Brake: 0-{max_brake:.1f}%")
        
        # Setup track plot
        first_driver = list(drivers_data.keys())[0]
        tel = drivers_data[first_driver]['telemetry']
        
        if 'X' in tel.columns and 'Y' in tel.columns:
            track_x_raw = tel['X'].values
            track_y_raw = tel['Y'].values
            track_x, track_y = self.optimize_track_layout(track_x_raw, track_y_raw)
        else:
            n_points = len(tel)
            angles = np.linspace(0, 2*np.pi, n_points)
            track_x = 1000 * np.cos(angles)
            track_y = 1000 * np.sin(angles)
        
        # Plot track outline
        ax_track.plot(track_x, track_y, 'gray', linewidth=3, alpha=0.4)
        ax_track.set_aspect('equal')
        ax_track.set_title('Track Dominance')
        ax_track.grid(True, alpha=0.3)
        
        # Add padding around track
        track_padding = 0.1
        x_range = np.max(track_x) - np.min(track_x)
        y_range = np.max(track_y) - np.min(track_y)
        
        ax_track.set_xlim(np.min(track_x) - track_padding * x_range, 
                          np.max(track_x) + track_padding * x_range)
        ax_track.set_ylim(np.min(track_y) - track_padding * y_range, 
                          np.max(track_y) + track_padding * y_range)
        
        # Add legend 
        legend_elements = []
        for driver, data in drivers_data.items():
            legend_elements.append(Line2D([0], [0], color=data['color'], lw=4, 
                                        label=f"{driver}"))
        ax_track.legend(handles=legend_elements, loc='upper right', fontsize=8)
        
        # Setup telemetry plots
        ax_speed.set_xlim(0, max_distance)
        ax_speed.set_ylim(0, max_speed * 1.05)
        ax_speed.set_title('Speed')
        ax_speed.set_ylabel('Speed (km/h)')
        ax_speed.set_xlabel('Distance (m)')
        ax_speed.grid(True, alpha=0.3)
        
        ax_throttle.set_xlim(0, max_distance)
        ax_throttle.set_ylim(0, max(max_throttle * 1.05, 100))
        ax_throttle.set_title('Throttle')
        ax_throttle.set_ylabel('Throttle (%)')
        ax_throttle.set_xlabel('Distance (m)')
        ax_throttle.grid(True, alpha=0.3)
        
        brake_max = max(max_brake * 1.2, 5)
        ax_brake.set_xlim(0, max_distance)
        ax_brake.set_ylim(0, brake_max)
        ax_brake.set_title('Brake')
        ax_brake.set_ylabel('Brake (%)')
        ax_brake.set_xlabel('Distance (m)')
        ax_brake.grid(True, alpha=0.3)
        
        return fig, ax_track, ax_speed, ax_throttle, ax_brake, track_x, track_y
    
    def initialize_animation_objects(self, drivers_data, ax_track, ax_speed, ax_throttle, ax_brake, track_x, track_y):
        """Initialize cars and individual driver traces with dynamic z-ordering"""
        
        car_markers = {}
        telemetry_collections = {}
        
        # Calculate car size
        track_range = max(np.max(track_x) - np.min(track_x), np.max(track_y) - np.min(track_y))
        car_size = track_range * 0.02
        
        # Base z-order for telemetry traces
        base_zorder = 5
        
        for i, (driver, data) in enumerate(drivers_data.items()):
            color = data['color']
            
            # Car marker
            car = Circle((track_x[0], track_y[0]), car_size, color=color, alpha=0.9, zorder=10)
            ax_track.add_patch(car)
            car_markers[driver] = car
            
            # Individual LineCollections for each driver (one per plot)
            speed_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            throttle_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            brake_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            
            ax_speed.add_collection(speed_collection)
            ax_throttle.add_collection(throttle_collection)
            ax_brake.add_collection(brake_collection)
            
            telemetry_collections[driver] = {
                'speed': speed_collection,
                'throttle': throttle_collection,
                'brake': brake_collection
            }
        
        # Track dominance trace (always on top)
        track_collection = LineCollection([], linewidths=6, alpha=0.8, zorder=20)
        ax_track.add_collection(track_collection)
        
        return car_markers, telemetry_collections, track_collection
    
    def animate_frame(self, frame, drivers_data, car_markers, telemetry_collections, track_collection, 
                     track_x, track_y, sector_colors, sector_dominant_drivers):
        """Update animation with individual driver traces and dynamic z-ordering"""
        
        # Update cars
        for driver, data in drivers_data.items():
            telemetry = data['telemetry']
            
            if frame >= len(telemetry):
                continue
                
            # Update car position
            progress = frame / len(telemetry)
            idx = min(int(progress * (len(track_x) - 1)), len(track_x) - 1)
            x_pos = track_x[idx]
            y_pos = track_y[idx]
            
            car_markers[driver].center = (x_pos, y_pos)
        
        # Update car z-orders based on current sector dominance
        if frame < len(sector_dominant_drivers):
            dominant_driver = sector_dominant_drivers[frame]
            
            # Set all cars to lower z-order
            for driver, marker in car_markers.items():
                marker.set_zorder(10)
                
            # Bring dominant driver's car to front
            if dominant_driver in car_markers:
                car_markers[dominant_driver].set_zorder(15)
        
        # Update traces
        if frame > 1:
            # Track dominance trace
            track_segments = []
            track_colors = []
            
            for i in range(min(frame - 1, len(track_x) - 1)):
                if i < len(sector_colors):
                    segment = [[track_x[i], track_y[i]], [track_x[i+1], track_y[i+1]]]
                    track_segments.append(segment)
                    track_colors.append(sector_colors[i])
            
            track_collection.set_segments(track_segments)
            track_collection.set_colors(track_colors)
            
            # Update telemetry z-orders based on current sector dominance
            current_dominant = sector_dominant_drivers[min(frame-1, len(sector_dominant_drivers)-1)]
            
            # Set base z-orders for all drivers
            base_zorder = 5
            for i, driver in enumerate(drivers_data.keys()):
                for collection_type in ['speed', 'throttle', 'brake']:
                    telemetry_collections[driver][collection_type].set_zorder(base_zorder + i)
            
            # Bring current dominant driver's traces to front
            if current_dominant in telemetry_collections:
                dominant_zorder = base_zorder + 10  # Higher than all others
                for collection_type in ['speed', 'throttle', 'brake']:
                    telemetry_collections[current_dominant][collection_type].set_zorder(dominant_zorder)
            
            # Update individual driver traces
            for driver, data in drivers_data.items():
                telemetry = data['telemetry']
                current_data = telemetry.iloc[:frame+1]
                
                if len(current_data) > 1:
                    distances = current_data['Distance'].values
                    speeds = current_data['Speed'].values
                    throttles = current_data['Throttle'].values
                    brakes = current_data['Brake'].values
                    
                    # Create segments for this driver's data
                    speed_segments = []
                    throttle_segments = []
                    brake_segments = []
                    
                    for i in range(len(distances) - 1):
                        # Speed segments
                        speed_segment = [[distances[i], speeds[i]], [distances[i+1], speeds[i+1]]]
                        speed_segments.append(speed_segment)
                        
                        # Throttle segments
                        throttle_segment = [[distances[i], throttles[i]], [distances[i+1], throttles[i+1]]]
                        throttle_segments.append(throttle_segment)
                        
                        # Brake segments
                        brake_segment = [[distances[i], brakes[i]], [distances[i+1], brakes[i+1]]]
                        brake_segments.append(brake_segment)
                    
                    # Update this driver's collections with their own color
                    driver_color = data['color']
                    colors = [driver_color] * len(speed_segments)
                    
                    telemetry_collections[driver]['speed'].set_segments(speed_segments)
                    telemetry_collections[driver]['speed'].set_colors(colors)
                    
                    telemetry_collections[driver]['throttle'].set_segments(throttle_segments)
                    telemetry_collections[driver]['throttle'].set_colors(colors)
                    
                    telemetry_collections[driver]['brake'].set_segments(brake_segments)
                    telemetry_collections[driver]['brake'].set_colors(colors)
        
        return []
    
    def run_simulation(self, year=2025, round_num=16):
        """Run the complete simulation"""
        
        # Load data
        drivers_data, session = self.load_data(year, round_num)
        if not drivers_data:
            print("No data available")
            return None
            
        print(f"Loaded data for: {list(drivers_data.keys())}")
        
        # Calculate sector dominance
        sector_colors, sector_dominant_drivers = self.calculate_sector_dominance(drivers_data)
        
        # Setup plots
        fig, ax_track, ax_speed, ax_throttle, ax_brake, track_x, track_y = \
            self.setup_plots(drivers_data, session)
        
        # Initialize animation objects
        car_markers, telemetry_collections, track_collection = \
            self.initialize_animation_objects(drivers_data, ax_track, ax_speed, ax_throttle, ax_brake, track_x, track_y)
        
        # Create animation
        min_length = min([len(data['telemetry']) for data in drivers_data.values()])
        print(f"Animation frames: {min_length}")
        
        anim = animation.FuncAnimation(
            fig,
            self.animate_frame,
            frames=min_length,
            fargs=(drivers_data, car_markers, telemetry_collections, track_collection, 
                   track_x, track_y, sector_colors, sector_dominant_drivers),
            interval=75,
            repeat=True
        )
        
        plt.show()
        return anim

# Run the simulator
if __name__ == "__main__":
    simulator = F1LaptimeSimulatorLayeredDominance()
    anim = simulator.run_simulation(year=2025, round_num=16)