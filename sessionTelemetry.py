import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches
import warnings
import os

warnings.filterwarnings('ignore')

class F1AnimationTool:
    def __init__(self):
        cache_dir = './cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"Created cache directory: {cache_dir}")
        
        fastf1.Cache.enable_cache(cache_dir)
    
    def safe_total_seconds(self, time_diff):
        if hasattr(time_diff, 'total_seconds'):
            return time_diff.total_seconds()
        else:
            return float(time_diff / np.timedelta64(1, 's'))

    def format_laptime(self, laptime_delta):
        if pd.isna(laptime_delta):
            return "No Time"
        
        total_seconds = self.safe_total_seconds(laptime_delta)
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        return f"{minutes}:{seconds:06.3f}"

    def load_data(self, year, round_num, session_name, selected_drivers=None):
        print(f"Loading {year} Round {round_num} {session_name} data...")
        
        session = fastf1.get_session(year, round_num, session_name)
        session.load()
        
        driver_colors = {
            'ALB': '#005aff', 'SAI': '#24ffff', 'LEC': '#dc0000', 'HAD': '#2b4562',
            'COL': '#ff117c', 'ALO': '#006f62', 'RUS': '#24ffff', 'OCO': "#6A6868",
            'STR': '#00413b', 'NOR': '#FF8700', 'HAM': '#ff2800', 'VER': '#23326A',
            'HUL': '#00e701', 'BEA': "#605e5e", 'PIA': '#FFD580', 'GAS': '#fe86bc',
            'LAW': "#50a8ac", 'ANT': "#a1fafa", 'TSU': '#356cac', 'BOR': '#008d01'
        }
        
        results = None
        
        if selected_drivers:
            available_drivers = session.results['Abbreviation'].tolist()
            print(f"Available drivers: {available_drivers}")
            
            valid_drivers = []
            for driver in selected_drivers:
                if driver.upper() in available_drivers:
                    valid_drivers.append(driver.upper())
                else:
                    print(f"Warning: Driver '{driver}' not found.")
            
            if len(valid_drivers) < 2:
                print("Error: Need at least 2 valid drivers. Using top 3 instead.")
                selected_drivers = None
            else:
                results = session.results[session.results['Abbreviation'].isin(valid_drivers)]
                print(f"Selected drivers: {valid_drivers}")
        
        if not selected_drivers:
            driver_fastest_laps = []
            
            for _, result in session.results.iterrows():
                driver = result['Abbreviation']
                driver_laps = session.laps.pick_driver(driver)
                
                if len(driver_laps) > 0:
                    fastest_lap = driver_laps.pick_fastest()
                    if fastest_lap is not None and not fastest_lap.empty and pd.notna(fastest_lap.get('LapTime')):
                        lap_time = self.safe_total_seconds(fastest_lap['LapTime'])
                        driver_fastest_laps.append({
                            'driver': driver,
                            'laptime': lap_time,
                            'driver_abbr': driver,
                            'team': result['TeamName']
                        })
            
            driver_fastest_laps.sort(key=lambda x: x['laptime'])
            
            top_3 = driver_fastest_laps[:3]
            
            print(f"Top 3 fastest drivers in session:")
            for i, item in enumerate(top_3):
                minutes = int(item['laptime'] // 60)
                seconds = item['laptime'] % 60
                print(f"  {i+1}. {item['driver']}: {minutes}:{seconds:06.3f}")
            
            top_3_drivers = [item['driver'] for item in top_3]
            results = session.results[session.results['Abbreviation'].isin(top_3_drivers)]
            results = results.set_index('Abbreviation').loc[top_3_drivers].reset_index()
        
        drivers_data = {}
        
        for i, (_, result) in enumerate(results.iterrows()):
            driver = result['Abbreviation']
            
            driver_laps = session.laps.pick_driver(driver)
            
            if len(driver_laps) == 0:
                print(f"Warning: {driver} has no laps, skipping...")
                continue
            
            fastest_lap = driver_laps.pick_fastest()
            
            if fastest_lap is None or fastest_lap.empty or pd.isna(fastest_lap.get('LapTime')):
                print(f"Warning: {driver} has no valid laps, skipping...")
                continue
            
            telemetry = fastest_lap.get_telemetry()
            if len(telemetry) > 0:
                color = driver_colors.get(driver, ['red', 'blue', 'green'][i])
                
                drivers_data[driver] = {
                    'telemetry': telemetry,
                    'color': color,
                    'team': result['TeamName'],
                    'laptime': fastest_lap['LapTime'],
                    'position': i + 1
                }
                
                print(f"{driver}: Using lap with time {self.format_laptime(fastest_lap['LapTime'])}")
        
        return drivers_data, session

    def optimize_track_layout(self, track_x, track_y):
        track_x_centered = track_x - np.mean(track_x)
        track_y_centered = track_y - np.mean(track_y)
        
        best_rotation = 0
        best_width_ratio = 0
        
        for angle_deg in range(0, 180, 10):
            angle_rad = np.radians(angle_deg)
            
            x_rot = track_x_centered * np.cos(angle_rad) - track_y_centered * np.sin(angle_rad)
            y_rot = track_x_centered * np.sin(angle_rad) + track_y_centered * np.cos(angle_rad)
            
            rot_width = np.max(x_rot) - np.min(x_rot)
            rot_height = np.max(y_rot) - np.min(y_rot)
            
            width_ratio = rot_width / (rot_height + 0.001)
            
            if width_ratio > best_width_ratio:
                best_width_ratio = width_ratio
                best_rotation = angle_deg
                track_x_rotated = x_rot
                track_y_rotated = y_rot
        
        return track_x_rotated, track_y_rotated

    def calculate_sector_dominance(self, drivers_data, num_sectors=100):
        min_length = min([len(data['telemetry']) for data in drivers_data.values()])
        sector_size = max(1, min_length // num_sectors)
        
        sector_colors = []
        sector_dominant_drivers = []
        
        for i in range(0, min_length, sector_size):
            sector_end = min(i + sector_size, min_length)
            sector_speeds = {}
            
            for driver, data in drivers_data.items():
                telemetry = data['telemetry']
                sector_tel = telemetry.iloc[i:sector_end]
                
                if len(sector_tel) > 0:
                    avg_speed = sector_tel['Speed'].mean()
                    sector_speeds[driver] = avg_speed
            
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

    def setup_plots(self, drivers_data, session):
        fig = plt.figure(figsize=(20, 14))
        
        gs = fig.add_gridspec(3, 2, width_ratios=[1.2, 0.8], height_ratios=[1, 1, 1])
        
        fig.subplots_adjust(top=0.88, bottom=0.08, hspace=0.4, wspace=0.25, left=0.06, right=0.90)
        
        sorted_drivers = sorted(drivers_data.items(), key=lambda x: x[1]['position'])
        
        fig.text(0.5, 0.96, f"{session.event['EventName']} - Driver Comparison", 
                ha='center', fontsize=16, fontweight='bold')
        
        if len(sorted_drivers) == 2:
            x_positions = [0.35, 0.60]
        elif len(sorted_drivers) == 3:
            x_positions = [0.25, 0.50, 0.75]
        else:
            total_width = 0.6
            spacing = total_width / (len(sorted_drivers) - 1) if len(sorted_drivers) > 1 else 0
            x_start = 0.5 - total_width / 2
            x_positions = [x_start + i * spacing for i in range(len(sorted_drivers))]
        
        for i, (driver, data) in enumerate(sorted_drivers):
            x_pos = x_positions[i]
            position = data['position']
            laptime_str = self.format_laptime(data['laptime'])
            team = data['team']
            
            rect = mpatches.Rectangle((x_pos - 0.01, 0.915), 0.02, 0.015, 
                                     transform=fig.transFigure, 
                                     color=data['color'], 
                                     clip_on=False, zorder=10)
            fig.patches.append(rect)
            
            fig.text(x_pos + 0.015, 0.9225, 
                    f"P{position}: {driver} ({team}) - {laptime_str}",
                    ha='left', fontsize=11, fontweight='bold', va='center')
        
        ax_track = fig.add_subplot(gs[0:2, 0])
        ax_delta = fig.add_subplot(gs[2, 0])
        ax_speed = fig.add_subplot(gs[0, 1])
        ax_throttle = fig.add_subplot(gs[1, 1])
        ax_brake = fig.add_subplot(gs[2, 1])
        
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
        
        max_distance = max(all_distances)
        max_speed = max(all_speeds)
        max_throttle = max(all_throttles)
        max_brake = max(all_brakes)
        
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
        
        ax_track.plot(track_x, track_y, 'gray', linewidth=3, alpha=0.4)
        ax_track.set_aspect('equal')
        ax_track.set_title('Track Dominance', fontsize=12, pad=15)
        ax_track.grid(True, alpha=0.3)
        
        ax_track.set_xticks([])
        ax_track.set_yticks([])
        ax_track.set_xticklabels([])
        ax_track.set_yticklabels([])
        
        track_padding = 0.1
        x_range = np.max(track_x) - np.min(track_x)
        y_range = np.max(track_y) - np.min(track_y)
        
        ax_track.set_xlim(np.min(track_x) - track_padding * x_range, 
                          np.max(track_x) + track_padding * x_range)
        ax_track.set_ylim(np.min(track_y) - track_padding * y_range, 
                          np.max(track_y) + track_padding * y_range)
        
        ax_speed.set_xlim(0, max_distance)
        ax_speed.set_ylim(0, max_speed * 1.05)
        ax_speed.set_title('Speed', fontsize=12, pad=15)
        ax_speed.set_ylabel('Speed (km/h)', fontsize=12)
        ax_speed.grid(True, alpha=0.3)
        ax_speed.tick_params(axis='both', labelsize=10)
        
        ax_throttle.set_xlim(0, max_distance)
        ax_throttle.set_ylim(0, max(max_throttle * 1.05, 100))
        ax_throttle.set_title('Throttle', fontsize=12, pad=15)
        ax_throttle.set_ylabel('Throttle (%)', fontsize=12)
        ax_throttle.grid(True, alpha=0.3)
        ax_throttle.tick_params(axis='both', labelsize=10)
        
        ax_brake.set_xlim(0, max_distance)
        ax_brake.set_ylim(0, 1.1)
        ax_brake.set_title('Brake', fontsize=12, pad=15)
        ax_brake.set_ylabel('Brake (On/Off)', fontsize=12)
        ax_brake.set_xlabel('Distance (m)', fontsize=12)
        ax_brake.grid(True, alpha=0.3)
        ax_brake.tick_params(axis='both', labelsize=10)
        
        ax_delta.set_xlim(0, max_distance)
        ax_delta.set_ylim(-1.0, 1)
        ax_delta.set_title('Time Delta vs Fastest Driver', fontsize=12, pad=15)
        ax_delta.set_ylabel('Delta (s)', fontsize=12)
        ax_delta.set_xlabel('Distance (m)', fontsize=12)
        ax_delta.grid(True, alpha=0.3)
        ax_delta.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=2)
        ax_delta.tick_params(axis='both', labelsize=10)
        
        return fig, ax_track, ax_speed, ax_throttle, ax_brake, ax_delta, track_x, track_y

    def initialize_animation_objects(self, drivers_data, ax_track, ax_speed, ax_throttle, ax_brake, ax_delta, track_x, track_y):
        car_markers = {}
        telemetry_collections = {}
        
        track_range = max(np.max(track_x) - np.min(track_x), np.max(track_y) - np.min(track_y))
        car_size = track_range * 0.02
        
        base_zorder = 5
        
        reference_driver = min(drivers_data.keys(), 
                              key=lambda d: self.safe_total_seconds(drivers_data[d]['laptime']))
        
        reference_telemetry = drivers_data[reference_driver]['telemetry']
        
        for i, (driver, data) in enumerate(drivers_data.items()):
            color = data['color']
            
            car = Circle((track_x[0], track_y[0]), car_size, color=color, alpha=0.9, zorder=10)
            ax_track.add_patch(car)
            car_markers[driver] = car
            
            speed_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            throttle_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            brake_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            delta_collection = LineCollection([], linewidths=3, colors=[color], alpha=0.9, zorder=base_zorder + i)
            
            ax_speed.add_collection(speed_collection)
            ax_throttle.add_collection(throttle_collection)
            ax_brake.add_collection(brake_collection)
            ax_delta.add_collection(delta_collection)
            
            telemetry = data['telemetry']
            distances = telemetry['Distance'].values
            
            if driver != reference_driver:
                ref_distances = reference_telemetry['Distance'].values
                ref_times = reference_telemetry['Time'].values
                driver_times = telemetry['Time'].values
                
                ref_elapsed = np.array([self.safe_total_seconds(t - ref_times[0]) for t in ref_times])
                driver_elapsed = np.array([self.safe_total_seconds(t - driver_times[0]) for t in driver_times])
                
                deltas = np.zeros(len(distances))
                for j, dist in enumerate(distances):
                    closest_idx = np.argmin(np.abs(ref_distances - dist))
                    if closest_idx < len(ref_elapsed):
                        deltas[j] = driver_elapsed[j] - ref_elapsed[closest_idx]
                
                window_size = 15
                smoothed_deltas = np.copy(deltas)
                for j in range(len(deltas)):
                    start = max(0, j - window_size // 2)
                    end = min(len(deltas), j + window_size // 2 + 1)
                    smoothed_deltas[j] = np.mean(deltas[start:end])
                
                data['precomputed_deltas'] = smoothed_deltas
            else:
                data['precomputed_deltas'] = np.zeros(len(distances))
            
            telemetry_collections[driver] = {
                'speed': speed_collection,
                'throttle': throttle_collection,
                'brake': brake_collection,
                'delta': delta_collection
            }
        
        track_collection = LineCollection([], linewidths=6, alpha=0.8, zorder=20)
        ax_track.add_collection(track_collection)
        
        return car_markers, telemetry_collections, track_collection, reference_driver

    def animate_frame(self, frame, drivers_data, car_markers, telemetry_collections, track_collection, 
                     track_x, track_y, sector_colors, sector_dominant_drivers, reference_driver):
        
        max_lap_time = max([self.safe_total_seconds(d['laptime']) for d in drivers_data.values()])
        min_telemetry_length = min([len(d['telemetry']) for d in drivers_data.values()])
        time_per_frame = max_lap_time / min_telemetry_length
        current_elapsed_time = frame * time_per_frame
        
        track_segments = []
        track_colors = []
        
        artists = []
        
        for driver, data in drivers_data.items():
            telemetry = data['telemetry']
            
            if len(telemetry) == 0:
                continue
                
            start_time = telemetry['Time'].iloc[0]
            elapsed_times = np.array([self.safe_total_seconds(t - start_time) for t in telemetry['Time']])
            
            if current_elapsed_time <= elapsed_times[-1]:
                time_idx = np.argmin(np.abs(elapsed_times - current_elapsed_time))
                time_idx = min(time_idx, len(telemetry) - 1)
            else:
                time_idx = len(telemetry) - 1
            
            track_progress = time_idx / (len(telemetry) - 1) if len(telemetry) > 1 else 0
            track_idx = min(int(track_progress * (len(track_x) - 1)), len(track_x) - 1)
            
            x_pos = track_x[track_idx]
            y_pos = track_y[track_idx]
            car_markers[driver].center = (x_pos, y_pos)
            artists.append(car_markers[driver])
        
        if frame < len(sector_dominant_drivers):
            dominant_driver = sector_dominant_drivers[frame]
            
            for driver, marker in car_markers.items():
                marker.set_zorder(10)
                
            if dominant_driver in car_markers:
                car_markers[dominant_driver].set_zorder(15)
        
        if frame > 10:
            for i in range(min(frame - 1, len(track_x) - 1)):
                if i < len(sector_colors):
                    segment = [[track_x[i], track_y[i]], [track_x[i+1], track_y[i+1]]]
                    track_segments.append(segment)
                    track_colors.append(sector_colors[i])
            
            current_dominant = sector_dominant_drivers[min(frame-1, len(sector_dominant_drivers)-1)]
            
            base_zorder = 5
            for i, driver in enumerate(drivers_data.keys()):
                for collection_type in ['speed', 'throttle', 'brake', 'delta']:
                    telemetry_collections[driver][collection_type].set_zorder(base_zorder + i)
            
            if current_dominant in telemetry_collections:
                dominant_zorder = base_zorder + 10
                for collection_type in ['speed', 'throttle', 'brake', 'delta']:
                    telemetry_collections[current_dominant][collection_type].set_zorder(dominant_zorder)
            
            for driver, data in drivers_data.items():
                telemetry = data['telemetry']
                
                if frame >= len(telemetry):
                    current_frame = len(telemetry) - 1
                else:
                    current_frame = frame
                
                if current_frame > 10:
                    distances = telemetry['Distance'].values[:current_frame+1]
                    speeds = telemetry['Speed'].values[:current_frame+1]
                    throttles = telemetry['Throttle'].values[:current_frame+1]
                    brakes = telemetry['Brake'].values[:current_frame+1]
                    deltas = data['precomputed_deltas'][:current_frame+1]
                    
                    speed_segments = [[[distances[i], speeds[i]], [distances[i+1], speeds[i+1]]] 
                                     for i in range(len(distances) - 1)]
                    throttle_segments = [[[distances[i], throttles[i]], [distances[i+1], throttles[i+1]]] 
                                        for i in range(len(distances) - 1)]
                    brake_segments = [[[distances[i], brakes[i]], [distances[i+1], brakes[i+1]]] 
                                     for i in range(len(distances) - 1)]
                    delta_segments = [[[distances[i], deltas[i]], [distances[i+1], deltas[i+1]]] 
                                     for i in range(len(distances) - 1)]
                    
                    driver_color = data['color']
                    colors = [driver_color] * len(speed_segments)
                    
                    telemetry_collections[driver]['speed'].set_segments(speed_segments)
                    telemetry_collections[driver]['speed'].set_colors(colors)
                    
                    telemetry_collections[driver]['throttle'].set_segments(throttle_segments)
                    telemetry_collections[driver]['throttle'].set_colors(colors)
                    
                    telemetry_collections[driver]['brake'].set_segments(brake_segments)
                    telemetry_collections[driver]['brake'].set_colors(colors)
                    
                    telemetry_collections[driver]['delta'].set_segments(delta_segments)
                    telemetry_collections[driver]['delta'].set_colors(colors)
                    
                    artists.append(telemetry_collections[driver]['speed'])
                    artists.append(telemetry_collections[driver]['throttle'])
                    artists.append(telemetry_collections[driver]['brake'])
                    artists.append(telemetry_collections[driver]['delta'])
        
        track_collection.set_segments(track_segments)
        track_collection.set_colors(track_colors)
        artists.append(track_collection)
        
        return artists

    def run_animation(self, year, round_num, session_name, selected_drivers=None):
        drivers_data, session = self.load_data(year, round_num, session_name, selected_drivers)
        if not drivers_data:
            print("No data available")
            return None
            
        print(f"Loaded data for: {list(drivers_data.keys())}")
        
        print("Pre-calculating deltas...")
        sector_colors, sector_dominant_drivers = self.calculate_sector_dominance(drivers_data)
        
        fig, ax_track, ax_speed, ax_throttle, ax_brake, ax_delta, track_x, track_y = \
            self.setup_plots(drivers_data, session)
        
        car_markers, telemetry_collections, track_collection, reference_driver = \
            self.initialize_animation_objects(drivers_data, ax_track, ax_speed, ax_throttle, ax_brake, ax_delta, track_x, track_y)
        
        min_length = min([len(data['telemetry']) for data in drivers_data.values()])
        print(f"Animation frames: {min_length}")
        
        anim = animation.FuncAnimation(
            fig,
            self.animate_frame,
            frames=min_length,
            fargs=(drivers_data, car_markers, telemetry_collections, track_collection, 
                   track_x, track_y, sector_colors, sector_dominant_drivers, reference_driver),
            interval=20,
            repeat=True,
            blit=True
        )
        
        plt.show()
        return anim


def get_user_input():
    print("\n" + "="*60)
    print("F1 TELEMETRY ANIMATION")
    print("="*60)
    
    while True:
        try:
            year_input = input(f"\nEnter year (e.g., 2025): ").strip()
            if not year_input:
                print("Please enter a year.")
                continue
            year = int(year_input)
            
            if year < 2018 or year > 2025:
                print("Please enter a year between 2018-2025.")
                continue
            break
        except ValueError:
            print("Please enter a valid year.")
    
    while True:
        try:
            round_input = input(f"Enter round number (1-24): ").strip()
            if not round_input:
                print("Please enter a round number.")
                continue
            round_num = int(round_input)
            
            if round_num < 1 or round_num > 24:
                print("Please enter a round number between 1-24.")
                continue
            break
        except ValueError:
            print("Please enter a valid round number.")
    
    while True:
        session_input = input(f"Enter session (Q for Qualifying, R for Race, FP1, FP2, FP3): ").strip().upper()
        if session_input in ['Q', 'R', 'FP1', 'FP2', 'FP3']:
            session_name = session_input
            break
        print("Please enter Q, R, FP1, FP2, or FP3.")
    
    print(f"\nSelected: {year}, Round {round_num}, Session {session_name}")
    
    print("\nDriver Selection:")
    print("1. Top 3 drivers (default)")
    print("2. Select specific drivers to compare")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2.")
    
    selected_drivers = None
    if choice == '2':
        print("\nEnter driver abbreviations (e.g. VER, HAM, LEC)")
        driver_input = input("Enter 2 or 3 drivers separated by commas: ").strip()
        if driver_input:
            selected_drivers = [d.strip().upper() for d in driver_input.split(',') if d.strip()]
            if len(selected_drivers) < 2:
                print("Need at least 2 drivers. Using top 3 instead.")
                selected_drivers = None
            elif len(selected_drivers) > 3:
                print("Maximum 3 drivers. Using first 3 selected.")
                selected_drivers = selected_drivers[:3]
            else:
                print(f"Selected drivers: {selected_drivers}")
    
    return year, round_num, session_name, selected_drivers


if __name__ == "__main__":
    year, round_num, session_name, selected_drivers = get_user_input()
    
    tool = F1AnimationTool()
    
    print(f"\n=== RUNNING ANIMATION FOR {year} ROUND {round_num} {session_name} ===")
    anim = tool.run_animation(year=year, round_num=round_num, session_name=session_name, selected_drivers=selected_drivers)