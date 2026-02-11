# AI Coding Guidelines for Energy Demand Simulator

## Project Overview
This is a real-time energy demand simulation system built with Python, Pygame, and SimPy. It models a city's energy consumption through different building types (residential, commercial, industrial) with dynamic consumption patterns based on time, temperature, and population.

## Architecture
- **`motor_logico.py`**: Core simulation engine with consumption models, annual optimization, and SimPy discrete event simulation
- **`interfaz_visual.py`**: Pygame-based UI with real-time visualization, controls, and audio feedback
- **`config.py`**: UI layout constants, color palette, and simulation parameters

## Key Patterns & Conventions

### Building Consumption Model
Buildings calculate consumption using: `consumo = (población × factor_tipo) × factor_horario × factor_temperatura`
- Residential: peaks at 8 PM, moderate HVAC impact
- Commercial: peaks at 1 PM, office hours pattern
- Industrial: constant operation with morning peak, high machinery consumption

### Simulation Flow
- Real-time simulation advances minute-by-minute with configurable speed (1x, 2x, 4x)
- Annual optimization runs 365 days × 24 hours using SimPy for each substation type
- Optimization criteria: zero blackouts first, then lowest total cost

### UI Layout System
Uses absolute positioning with predefined rectangles:
- `HEADER_RECT`: Top status bar with time/temperature/consumption
- `SIDEBAR_RECT`: Right panel with substation controls and legend
- `GRID_RECT`: Main area for building visualization
- `GRAPH_RECT`: Bottom chart showing consumption history

### Color Coding
- **Cyan**: Energy/global consumption, UI accents
- **Amber**: Temperature, warnings
- **Red**: Blackouts, industrial buildings
- **Green**: Efficiency, commercial buildings
- **Blue**: Residential buildings

## Development Workflows

### Running the Simulator
```bash
python interfaz_visual.py
```
- Use speed controls in header to adjust simulation pace
- Switch substations via sidebar buttons
- "CALCULAR ÓPTIMO" runs annual comparison of all three substations

### Testing Logic
```bash
python motor_logico.py
```
Runs basic validation with sample city generation and consumption snapshots.

### Adding New Features
1. Define behavior in `motor_logico.py` first (consumption logic, simulation)
2. Add UI controls in `interfaz_visual.py` (buttons, display)
3. Update constants in `config.py` if needed
4. Test both real-time and annual simulation modes

## Common Tasks

### Modifying Consumption Formulas
Edit `Edificio.calcular_consumo()` in `motor_logico.py`:
- Update factor calculations for realistic energy patterns
- Test with `obtener_datos_snapshot()` for immediate feedback

### Adding Visual Effects
In `interfaz_visual.py`:
- Use `Particle` class for smoke/dust effects
- Add glow effects with `pygame.SRCALPHA` surfaces
- Integrate with building consumption levels

### Extending Substation Types
1. Add entry to `SUBESTACIONES` dict in `motor_logico.py`
2. Add to `SUBESTACIONES_CONFIG` in `config.py`
3. Update UI button generation in `SimulacionUI.init_layout()`

## Dependencies
- `pygame`: Graphics and audio
- `simpy`: Discrete event simulation
- Data science stack (numpy, pandas, matplotlib) available but minimally used

## File Structure Notes
- No traditional class hierarchy - functional design with main UI class
- Spanish variable names and comments throughout
- Real-time simulation with separate annual optimization mode
- Audio uses generated sine waves, not sound files