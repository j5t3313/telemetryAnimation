# F1 Qualifying Telemetry Simulator

A silly little script that creates animated visualizations comparing telemetry data from the top 3 drivers in Q3. Provides sector-by-sector dominance analysis with dynamic track visualization and telemetry plots.

## Features

### 🏎️ **Real-Time Animation**
- Animated representations of cars moving around the track layout
- Dynamic telemetry traces that build progressively
- Sector dominance visualization with color-coded track segments

### 📊 **Telemetry Analysis**
- **Speed Analysis**: Compare speed profiles throughout the lap
- **Throttle Data**: Visualize acceleration zones and driving styles
- **Brake Analysis**: Identify braking points and techniques
- **Track Dominance**: See which driver is fastest in each sector

### 🎨 **Visualization**
- Automatic track layout optimization and rotation
- Official team colors for each driver (hard coded because I don't like FastF1's color selection. Idc if it isn't optimal)
- Dynamic z-ordering to highlight dominant drivers
- Multi-panel dashboard with synchronized data

### 🏁 **Race Weekend Integration**
- Supports any F1 season and race weekend
- Automatic data fetching from official timing systems
- Top 3 Q3 drivers automatically selected
- Lap time formatting and position display

## Installation

### Prerequisites
```bash
pip install fastf1 pandas numpy matplotlib
```

### Dependencies
- **FastF1**: Official F1 timing data access
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib**: Plotting and animation

### Setup
1. Clone the repository:
```bash
git clone [https://github.com/j5t3313/telemetryAnimation.git]
cd f1-qualifying-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the simulator:
```bash
python qualiTelSimv2.py
```

## Usage

### Basic Usage
Run with default settings (2025 Monza Grand Prix):
```python
from qualiTelSimv2 import F1LaptimeSimulatorLayeredDominance

simulator = F1LaptimeSimulatorLayeredDominance()
animation = simulator.run_simulation()
```

### Custom Race Selection
```python
# 2024 Monaco Grand Prix
animation = simulator.run_simulation(year=2024, round_num=8)

# 2023 British Grand Prix  
animation = simulator.run_simulation(year=2023, round_num=10)
```

### Understanding the Output

The simulator creates a 2x2 dashboard with:

1. **Track Dominance** (Top Left): Shows the actual track layout with color-coded sectors indicating which driver was fastest in each section
2. **Speed Profile** (Top Right): Speed vs distance comparison for all three drivers
3. **Throttle Input** (Bottom Left): Throttle percentage throughout the lap
4. **Brake Input** (Bottom Right): Braking intensity and points

## How It Works

### Data Processing
1. **Data Acquisition**: Uses FastF1 to fetch official F1 timing data
2. **Driver Selection**: Automatically identifies top 3 Q3 performers
3. **Telemetry Processing**: Extracts speed, throttle, brake, and position data
4. **Track Optimization**: Rotates track layout for optimal viewing

### Animation System
- **Sector Analysis**: Divides lap into 100 sectors for granular dominance calculation
- **Dynamic Rendering**: Updates car positions and telemetry traces in real-time
- **Z-Order Management**: Brings dominant driver's data to the foreground
- **Color Coding**: Uses team colors for easy identification

### Technical Features
- **Automatic Caching**: Speeds up subsequent runs for the same race
- **Error Handling**: Graceful handling of missing data or connection issues
- **Memory Optimization**: Efficient data structures for smooth animation
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Configuration

### Customizable Parameters

```python
# Animation speed (milliseconds between frames)
interval=75  # Default: 75ms

# Number of sectors for dominance analysis
num_sectors=100  # Default: 100 sectors

# Track optimization settings
track_padding=0.1  # Visual padding around track
```

### Color Scheme
The simulator uses colors I picked:
- McLaren: Orange (#FF8700) and Blue (#FFD580)
- Red Bull: Navy (#23326A)
- Mercedes: Cyan (#24ffff)
- Ferrari: Red (#dc0000)
- And more...

## Performance Tips

1. **First Run**: Initial data download may take time - cached for subsequent runs
2. **System Resources**: Close other applications for smoother animation
3. **Data Quality**: Some sessions may have limited telemetry data. F1's public data stream is very low-resolution. 

## Troubleshooting

### Common Issues

**"No data available"**
- Check if the race weekend has occurred
- Verify qualifying session took place
- Some historical races may have limited data

**Animation lag**
- Reduce `num_sectors` parameter
- Increase `interval` time
- Close other resource-intensive applications

**Import errors**
- Ensure all dependencies are installed: `pip install fastf1 pandas numpy matplotlib`
- Check Python version compatibility (3.7+)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **FastF1 Project**: For providing excellent F1 data access
- **Formula 1**: For the amazing sport and data availability
- **Matplotlib**: For powerful visualization capabilities

## Disclaimer

This project is for educational and analytical purposes only. It is not affiliated with Formula 1, FIA, or any F1 teams. All data is sourced from publicly available official timing systems.

