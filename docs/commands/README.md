# RevitMCPBridge Command Library

Pre-built Python scripts for common Revit automation tasks.

## Quick Start

```bash
cd /mnt/d/RevitMCPBridge2026/commands

# Test your connection
python examples/quick_start.py

# Run a model audit
python extraction/model_audit.py

# Create building walls
python workflows/building_creator.py
```

## Folder Structure

```
commands/
├── core/                    # Core library (import this)
│   ├── __init__.py
│   └── revit_mcp.py        # Main RevitMCP client class
│
├── workflows/              # Complete workflow scripts
│   ├── building_creator.py # Create building shells
│   └── sheet_automation.py # Create and populate sheets
│
├── extraction/             # Data extraction scripts
│   └── model_audit.py      # Full model audit/report
│
├── automation/             # Batch automation scripts
│   └── (coming soon)
│
└── examples/               # Example scripts
    └── quick_start.py      # Connection test & examples
```

## Using the Core Library

```python
from core.revit_mcp import RevitMCP

# Connect to Revit
revit = RevitMCP()

# Get data
levels = revit.get_levels()
walls = revit.get_walls()
rooms = revit.get_rooms()

# Create elements
revit.create_wall(
    start=(0, 0),
    end=(20, 0),
    height=10,
    level_id=levels[0]["id"]
)

# Create rectangular room (4 walls)
revit.create_rectangular_room(
    x=0, y=0,
    width=20, depth=15,
    height=10,
    level_id=levels[0]["id"]
)
```

## Available Methods

### Levels
- `get_levels()` - List all levels
- `create_level(name, elevation)` - Create new level

### Walls
- `get_walls()` - List all walls
- `get_wall_types()` - List wall types
- `create_wall(start, end, height, level_id)` - Create single wall
- `create_walls_batch(walls)` - Create multiple walls
- `create_rectangular_room(x, y, width, depth, height, level_id)` - Create 4-wall room

### Rooms
- `get_rooms()` - List all rooms
- `create_room(level_id, location, name, number)` - Create room

### Doors & Windows
- `get_door_types()` - List door types
- `get_window_types()` - List window types
- `place_door(wall_id, location, door_type_id)` - Place door
- `place_window(wall_id, location, window_type_id)` - Place window

### Views
- `get_views(view_type)` - List views (optionally by type)
- `create_floor_plan(level_id, name)` - Create floor plan
- `set_active_view(view_id)` - Switch active view
- `zoom_to_fit(view_id)` - Zoom to fit

### Sheets
- `get_sheets()` - List all sheets
- `create_sheet(number, name)` - Create sheet
- `place_view_on_sheet(sheet_id, view_id, location)` - Place view on sheet

### Families
- `get_family_types(category)` - List family types
- `place_family_instance(type_id, location, level_id, rotation)` - Place family

### Schedules
- `get_schedules()` - List schedules
- `create_schedule(name, category, fields)` - Create schedule
- `export_schedule_to_csv(schedule_id, file_path)` - Export to CSV

### Parameters
- `get_element_parameters(element_id)` - Get element parameters
- `set_parameter(element_id, param_name, value)` - Set parameter

### Utility
- `delete_element(element_id)` - Delete single element
- `delete_elements(element_ids)` - Delete multiple elements
- `get_project_info()` - Get project info
- `get_active_view()` - Get active view
- `call(method, **params)` - Call any MCP method

## Workflow Scripts

### Building Creator
Create complete building shells:

```python
from workflows.building_creator import (
    create_rectangular_building,
    create_simple_house,
    create_l_shaped_building
)

# Simple rectangular building
create_rectangular_building(
    width=30,
    depth=40,
    wall_height=10
)

# Multi-floor house
create_simple_house(
    width=30,
    depth=40,
    wall_height=10,
    num_floors=2
)

# L-shaped building
create_l_shaped_building(
    main_width=40,
    main_depth=30,
    wing_width=20,
    wing_depth=15,
    wall_height=10
)
```

### Sheet Automation
Create and manage sheets:

```python
from workflows.sheet_automation import (
    create_sheet_set,
    create_custom_sheets,
    place_views_on_sheet,
    auto_populate_sheets
)

# Create standard architectural sheets
create_sheet_set("architectural")

# Custom sheets
create_custom_sheets([
    {"number": "A101", "name": "FIRST FLOOR PLAN"},
    {"number": "A102", "name": "SECOND FLOOR PLAN"},
])

# Auto-place views on matching sheets
auto_populate_sheets()
```

### Model Audit
Extract model data:

```python
from extraction.model_audit import (
    full_audit,
    quick_stats,
    get_wall_summary,
    get_room_summary
)

# Full audit with report
report = full_audit(output_file="audit.json")

# Quick element counts
quick_stats()

# Specific summaries
walls = get_wall_summary()
rooms = get_room_summary()
```

## Error Handling

```python
from core.revit_mcp import RevitMCP, RevitMCPError

revit = RevitMCP()

try:
    result = revit.create_wall(...)
except RevitMCPError as e:
    print(f"Revit error: {e}")
```

## Requirements

- Python 3.8+
- Revit 2026 with RevitMCPBridge add-in loaded
- Windows (uses PowerShell for named pipe communication)

## Tips

1. **Always check connection first**: Run `quick_start.py` to verify Revit is responding
2. **Use batch operations**: When creating many elements, use batch methods or add `time.sleep(0.1)` between calls
3. **Get IDs first**: Most creation methods need level/type IDs - query them first
4. **Handle errors**: Wrap API calls in try/except for production scripts
