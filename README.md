# F1 Telemetry Animation Tool

An animated telemetry visualization tool for comparing F1 driver performance across any session. Creates animated traces showing speed, throttle, brake inputs, and time deltas with dynamic track dominance visualization.

## Features

### Animated Telemetry Traces
- Animated car positions moving around the track layout
- Progressive telemetry trace building as the lap unfolds
- Sector-by-sector dominance visualization with color-coded track segments
- Live time delta calculations against the fastest driver

### Telemetry Analysis
- **Speed Profile**: Compare speed throughout the lap
- **Throttle Input**: Visualize acceleration zones and driving styles
- **Brake Analysis**: Identify braking points and techniques
- **Time Delta**: Real-time gap analysis showing where time is gained or lost
- **Track Dominance**: Color-coded track showing which driver is fastest in each sector

### Visualization
- Automatic track layout optimization and rotation
- Team colors for driver identification
- Dynamic z-ordering highlighting the dominant driver in each sector
- Multi-panel dashboard with synchronized data
- Optimized animation performance with pre-computed calculations

### Session Support
- **Qualifying**: Compare Q3 performances
- **Practice**: Analyze FP1, FP2, FP3 sessions
- **Race**: Compare race pace and strategies
- Automatic selection of top 3 fastest drivers or manual driver selection
- Supports any F1 season from 2018 onwards

## Installation

### Prerequisites
```bash
pip install fastf1 pandas numpy matplotlib scipy
```

### Dependencies
- **FastF1**: Official F1 timing data access
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib**: Plotting and animation
- **SciPy**: Signal processing for telemetry analysis

### Setup
1. Clone the repository:
```bash
git clone [repository-url]
cd f1-telemetry-animation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the tool:
```bash
python f1_animation_tool.py
```

## Usage

### Interactive Mode
The tool provides an interactive command-line interface:
```
F1 TELEMETRY ANIMATION
============================================================

Enter year (e.g., 2025): 2024
Enter round number (1-24): 19
Enter session (Q for Qualifying, R for Race, FP1, FP2, FP3): Q

Driver Selection:
1. Top 3 drivers (default)
2. Select specific drivers to compare
Enter choice (1 or 2): 2

Enter driver abbreviations (e.g. VER, HAM, LEC)
Enter 2 or 3 drivers separated by commas: NOR, VER, PIA
```

### Programmatic Usage
```python
from f1_animation_tool import F1AnimationTool

tool = F1AnimationTool()

# Top 3 fastest drivers in FP1
anim = tool.run_animation(year=2024, round_num=19, session_name='FP1')

# Specific driver comparison in Qualifying
anim = tool.run_animation(
    year=2024, 
    round_num=19, 
    session_name='Q',
    selected_drivers=['VER', 'NOR', 'LEC']
)
```

### Understanding the Dashboard

The animation displays a synchronized multi-panel view:

1. **Track Dominance** (Top Left): Track layout with color-coded sectors showing which driver is fastest in each section. 

2. **Speed** (Top Right): Speed vs distance comparison. Lines build progressively showing each driver's speed profile.

3. **Throttle** (Middle Right): Throttle input percentage throughout the lap. Shows acceleration zones and driving style differences.

4. **Brake** (Bottom Right): Brake application intensity. Identifies braking points and technique variations.

5. **Time Delta** (Bottom Left): Running time difference vs the fastest driver. Positive values indicate time loss, negative values show time gain.

## How It Works

### Data Processing
1. **Data Acquisition**: Uses FastF1 to fetch official F1 timing data
2. **Driver Selection**: Automatically identifies top 3 fastest drivers in the selected session
3. **Telemetry Processing**: Extracts speed, throttle, brake, position, and timing data
4. **Track Optimization**: Rotates track layout for optimal horizontal viewing
5. **Delta Calculation**: Pre-computes time deltas for smooth animation performance

### Animation System
- **Sector Analysis**: Divides lap into 100 sectors for granular dominance calculation
- **Dynamic Rendering**: Updates car positions and telemetry traces frame-by-frame
- **Z-Order Management**: Brings dominant driver's data to the foreground in each sector
- **Color Coding**: Uses team colors for easy identification
- **Blit Optimization**: Only redraws changed elements for improved performance

### Performance Optimizations
- **Pre-computed Deltas**: All time differences calculated before animation starts
- **NumPy Operations**: Vectorized calculations for faster processing
- **Blit Mode**: Efficient rendering by updating only changed artists
- **Reduced Interval**: 20ms frame time for smooth animation

## Configuration

### Driver Colors
The tool uses custom team colors (hardcoded for consistent appearance):
- McLaren: Orange (#FF8700) and Papaya (#FFD580)
- Red Bull: Navy (#23326A)
- Mercedes: Cyan (#24ffff)
- Ferrari: Red (#dc0000)
- And more for all teams

### Animation Parameters
Default settings optimized for performance:
```python
interval=20  # 20ms between frames (50fps)
num_sectors=100  # Sector granularity for dominance
blit=True  # Fast rendering mode
```

## Performance Tips

1. **First Run**: Initial data download takes time but is cached for future runs
2. **System Resources**: Close other applications for smoother animation
3. **Data Quality**: F1's public telemetry stream is low-resolution compared to team data
4. **Session Selection**: Practice sessions may have incomplete data if drivers don't complete full laps

## Troubleshooting

### Common Issues

**"No data available"**
- Check if the race weekend has occurred
- Verify the session took place
- Some historical races may have limited telemetry data

**Animation performance issues**
- The optimized version should run smoothly on most systems
- Reduce window size if experiencing lag
- Ensure matplotlib backend is properly configured

**Driver selection errors**
- Verify driver abbreviations are correct (3-letter codes)
- Check that drivers participated in the selected session
- Use option 1 (top 3 automatic) if unsure of driver codes

**Import errors**
- Ensure all dependencies are installed
- Check Python version compatibility (3.7+)
- Update packages: `pip install --upgrade fastf1 pandas numpy matplotlib scipy`

## Technical Details

### Data Sources
- Official F1 timing data via FastF1 API
- Telemetry sampled at variable rates (typically 3-10 Hz)
- GPS coordinates for track layout visualization

### Coordinate System
- Track coordinates rotated for optimal viewing angle
- Distance measured in meters along racing line
- Time measured in seconds with microsecond precision

### Calculation Methods
- **Time Delta**: Interpolated comparison at matching distance points
- **Sector Dominance**: Average speed comparison over 100 equal segments
- **Smoothing**: 15-point moving average for delta visualization

## License

This project is licensed under the MIT License.

## Acknowledgments

- **FastF1 Project**: For providing excellent F1 data access
- **Formula 1**: For making timing data available
- **Matplotlib**: For powerful animation and visualization capabilities

This project is for educational and analytical purposes only. It is not affiliated with Formula 1, FIA, or any F1 teams. All data is sourced from publicly available official timing systems.

