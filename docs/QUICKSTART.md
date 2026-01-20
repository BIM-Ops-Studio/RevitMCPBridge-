# RevitMCPBridge2026 Quick Start Guide

Get up and running with RevitMCPBridge in 5 minutes.

## Prerequisites

- Revit 2026 installed
- .NET Framework 4.8
- Visual Studio 2022 (for building)

## Installation

### Option 1: Use Installer Script (Recommended)

```powershell
cd scripts/deploy
.\Install-RevitMCPBridge.ps1
```

### Option 2: Manual Installation

```bash
# Build the project
msbuild RevitMCPBridge2026.csproj /p:Configuration=Release

# Copy to Revit add-ins folder
copy bin\Release\RevitMCPBridge2026.dll "%APPDATA%\Autodesk\Revit\Addins\2026\"
copy RevitMCPBridge2026.addin "%APPDATA%\Autodesk\Revit\Addins\2026\"
```

## Verify Installation

1. Start Revit 2026
2. Open any project
3. Test the connection:

```python
import socket
import json

def call_revit(method, params=None):
    """Send a command to Revit via MCP Bridge."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 8765))
        request = json.dumps({"method": method, "params": params or {}})
        s.sendall(request.encode() + b'\n')
        response = s.recv(65536).decode()
        return json.loads(response)

# Test: Get version info
result = call_revit("getVersion")
print(result)
# Output: {"success": true, "version": "2.0.0", "revitVersion": "2026.2", ...}

# Test: Health check
result = call_revit("healthCheck")
print(result)
# Output: {"success": true, "status": "healthy", "documentOpen": true, ...}
```

## Common Operations

### Get Model Information

```python
# Get all levels
levels = call_revit("getLevels")
print(f"Found {len(levels['levels'])} levels")

# Get all walls
walls = call_revit("getWalls")
print(f"Found {len(walls['walls'])} walls")

# Get all rooms
rooms = call_revit("getRooms")
print(f"Found {len(rooms['rooms'])} rooms")
```

### Create Elements

```python
# Get available wall types first
wall_types = call_revit("getWallTypes")
wall_type_id = wall_types['wallTypes'][0]['id']

# Get level for placement
levels = call_revit("getLevels")
level_id = levels['levels'][0]['id']

# Create a wall (coordinates in feet)
result = call_revit("createWall", {
    "startX": 0.0,
    "startY": 0.0,
    "endX": 20.0,
    "endY": 0.0,
    "levelId": level_id,
    "height": 10.0,
    "wallTypeId": wall_type_id
})
print(f"Created wall with ID: {result['elementId']}")
```

### Query Elements

```python
# Get specific element by ID
element = call_revit("getElementById", {"elementId": 123456})
print(element)

# Get elements by category
doors = call_revit("getElements", {"category": "Doors"})
print(f"Found {len(doors['elements'])} doors")

# Get element location
location = call_revit("getElementLocation", {"elementId": 123456})
print(f"Location: ({location['x']}, {location['y']}, {location['z']})")
```

### Work with Views and Sheets

```python
# Get all views
views = call_revit("getViews")
print(f"Found {len(views['views'])} views")

# Get all sheets
sheets = call_revit("getSheets")
print(f"Found {len(sheets['sheets'])} sheets")

# Create a new sheet
result = call_revit("createSheet", {
    "sheetNumber": "A-101",
    "sheetName": "Floor Plan - Level 1"
})
print(f"Created sheet: {result['sheetNumber']}")

# Place a view on a sheet
call_revit("placeViewOnSheet", {
    "sheetId": result['sheetId'],
    "viewId": views['views'][0]['id'],
    "x": 1.5,
    "y": 1.0
})
```

### Export Data

```python
# Get schedule data
schedules = call_revit("getSchedules")
schedule_id = schedules['schedules'][0]['id']

data = call_revit("getScheduleData", {"scheduleId": schedule_id})
print(f"Schedule has {data['rowCount']} rows and {data['columnCount']} columns")

# Export to CSV
call_revit("exportScheduleToCSV", {
    "scheduleId": schedule_id,
    "filePath": "C:\\output\\schedule.csv"
})
```

## Python Helper Class

For convenience, here's a simple wrapper class:

```python
import socket
import json

class RevitMCP:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port

    def call(self, method, params=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            request = json.dumps({"method": method, "params": params or {}})
            s.sendall(request.encode() + b'\n')
            response = s.recv(65536).decode()
            return json.loads(response)

    # Convenience methods
    def get_levels(self):
        return self.call("getLevels")

    def get_walls(self):
        return self.call("getWalls")

    def get_rooms(self):
        return self.call("getRooms")

    def create_wall(self, start, end, level_id, height=10.0, wall_type_id=None):
        return self.call("createWall", {
            "startX": start[0], "startY": start[1],
            "endX": end[0], "endY": end[1],
            "levelId": level_id,
            "height": height,
            "wallTypeId": wall_type_id
        })

# Usage
revit = RevitMCP()
print(revit.get_levels())
```

## PowerShell Examples

```powershell
# Simple health check
$body = '{"method": "healthCheck", "params": {}}'
Invoke-RestMethod -Uri "http://localhost:8765" -Method POST -Body $body -ContentType "application/json"

# Get all levels
$body = '{"method": "getLevels", "params": {}}'
$result = Invoke-RestMethod -Uri "http://localhost:8765" -Method POST -Body $body -ContentType "application/json"
$result.levels | Format-Table
```

## Error Handling

All responses include a `success` field:

```python
result = call_revit("getElementById", {"elementId": 999999})
if not result.get('success'):
    print(f"Error: {result.get('error')}")
else:
    print(f"Element: {result['element']}")
```

## Available Methods

Run `getMethods` to get a list of all 437+ available methods:

```python
methods = call_revit("getMethods")
print(f"Total methods: {methods['count']}")
for method in methods['methods'][:10]:
    print(f"  - {method}")
```

Categories:
- **System** (6): Version, health, configuration
- **Elements** (14): Core element operations
- **Walls** (11): Wall creation and modification
- **Doors/Windows** (13): Opening placement
- **Rooms** (10): Room operations
- **Views** (12): View management
- **Sheets** (11): Sheet and viewport operations
- **Schedules** (30): Schedule operations
- And 30+ more categories...

See [docs/api/METHODS.md](api/METHODS.md) for complete API reference.

## Configuration

The bridge can be configured via `appsettings.json`:

```json
{
  "Pipe": {
    "Name": "RevitMCPBridge2026",
    "TimeoutMs": 30000
  },
  "Logging": {
    "Level": "Information"
  }
}
```

## Next Steps

1. Read the [full API reference](api/METHODS.md)
2. Check out the [usage guide](guides/USAGE_GUIDE.md) for advanced examples
3. Explore the [architecture documentation](ARCHITECTURE.md)

## Troubleshooting

**Connection refused:**
- Ensure Revit is running
- Check that the add-in loaded (look for "MCP Bridge" in Revit ribbon)
- Restart Revit

**Method not found:**
- Verify method name spelling
- Check that you have the latest DLL installed
- Run `getMethods` to see available methods

**Operation failed:**
- Check that a document is open in Revit
- Verify element IDs are valid
- Check for Revit dialogs that might be blocking

---

For more help, see the full documentation in `/docs` or file an issue on GitHub.
