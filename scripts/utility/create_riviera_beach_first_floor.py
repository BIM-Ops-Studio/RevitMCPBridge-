#!/usr/bin/env python3
"""
Riviera Beach 2-Story Prototype - First Floor Wall Creation
Based on Exhibit-B-1713_2-STORY_PROTOTYPE-BID_PERMIT-SET-092818.pdf

Building Dimensions (from A-100):
- Overall Width: 45'-4" (45.333 ft)
- Overall Depth: 28'-8" (28.667 ft)
- First Floor Height: 10'-0" (to 2nd floor)
- Ceiling Height 1: 9'-5.5" (fin ceiling 1)

Wall Types from A-100:
- W1: Exterior - 8" CMU + insulation + furring + GWB + stucco (~11")
- W2: Interior Load Bearing - 2x4 wood stud + GWB both sides (~5")
- W3: Interior Non-Bearing - 2x4 or 3-5/8" metal stud + GWB (~4-5")

Grid Lines (from A-100):
- A to B: 11'-4"
- B to C: 10'-8"
- C to D: 23'-4"
- 1 to 2: 7'-0"
- 2 to 3: variable
- 3 to 4: variable
- 4 to 5: variable

First Floor Rooms:
- 101: Garage (242 SF)
- 102: Utility Room (44 SF)
- 103: Pantry (2 SF)
- 104: Kitchen (204 SF)
- 105: Living Room (144 SF)
- 106: Dining Room (100 SF)
- 107: 1/2 Bath (35 SF)
- 108: Closet under stairs (68 SF)
- 109: Foyer (49 SF)
- EX-1: Porch (54 SF)
- EX-2: Rear Lanai (110 SF)
"""

import json
import time
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, params):
    """Send a request to the MCP server and return the response"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )

        # IMPORTANT: Use 'params' not 'parameters' - the server expects 'params'
        # Also, the server expects a newline at the end of the message
        request = {
            "method": method,
            "params": params
        }
        request_json = json.dumps(request) + "\n"

        win32file.WriteFile(handle, request_json.encode('utf-8'))
        result, data = win32file.ReadFile(handle, 64 * 1024)
        win32file.CloseHandle(handle)

        return json.loads(data.decode('utf-8'))
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running. Click 'Start MCP Server' in Revit."}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_result(result, description):
    """Print formatted result"""
    print(f"\n[{description}]")
    if result.get("success"):
        print("  SUCCESS")
        for key, value in result.items():
            if key != "success":
                print(f"  {key}: {value}")
    else:
        print(f"  FAILED: {result.get('error', 'Unknown error')}")
    return result.get("success", False)

# ============================================================================
# STEP 1: Test Connection & Get Levels
# ============================================================================
print("\n" + "="*80)
print("RIVIERA BEACH 2-STORY PROTOTYPE - FIRST FLOOR WALLS")
print("="*80)

print("\n1. Testing MCP connection...")
levels = send_mcp_request("getLevels", {})
if not print_result(levels, "Get Levels"):
    print("\nERROR: Cannot connect to Revit MCP Server.")
    print("Please ensure:")
    print("  1. Revit 2026 is open with a project")
    print("  2. Click 'Start MCP Server' in the Revit ribbon")
    sys.exit(1)

# Find First Floor level
# Note: API returns 'levelId' not 'id'
first_floor_level_id = None
level_list = levels.get("levels", [])
for level in level_list:
    name = level.get("name", "").lower()
    if "first" in name or "level 1" in name or name == "l1" or "1st" in name:
        first_floor_level_id = level.get("levelId")
        print(f"\n  Found First Floor Level: {level.get('name')} (ID: {first_floor_level_id})")
        break

if not first_floor_level_id and level_list:
    # Use first level if no "first floor" found
    first_floor_level_id = level_list[0].get("levelId")
    print(f"\n  Using level: {level_list[0].get('name')} (ID: {first_floor_level_id})")

# ============================================================================
# STEP 2: Wall Types - Skip query due to buffer truncation issue
# The MCP server will use default Basic wall type if not specified
# ============================================================================
print("\n2. Using default wall types (query skipped due to buffer issue)")
print("  Note: Revit will use 'Basic Wall' type for all walls")
# Don't specify wall type - let Revit use default

# ============================================================================
# STEP 3: Define Wall Geometry
# ============================================================================
print("\n3. Defining wall geometry from floor plan...")

# Building dimensions in feet (from A-100)
OVERALL_WIDTH = 45.333   # 45'-4"
OVERALL_DEPTH = 28.667   # 28'-8"
WALL_HEIGHT = 10.0       # 10'-0" first floor height

# Grid dimensions (approximate from plan)
# Grid A at X=0
# Grid B at X=11.333 (11'-4")
# Grid C at X=22.0 (11'-4" + 10'-8")
# Grid D at X=45.333 (22' + 23'-4")

GRID_A = 0.0
GRID_B = 11.333
GRID_C = 22.0
GRID_D = 45.333

# Grid 1 at Y=0
# Grid 5 at Y=28.667
GRID_1 = 0.0
GRID_5 = 28.667

# Exterior wall boundary points (polyline for closed loop)
# Format: [x, y, z] arrays - required by WallMethods.cs
# Note: Don't include closing point - closed=True handles that
exterior_boundary = [
    [0, 0, 0],                          # SW corner
    [OVERALL_WIDTH, 0, 0],              # SE corner
    [OVERALL_WIDTH, OVERALL_DEPTH, 0],  # NE corner
    [0, OVERALL_DEPTH, 0],              # NW corner
    # Don't repeat first point - closed=True will connect back
]

print(f"  Building size: {OVERALL_WIDTH}' x {OVERALL_DEPTH}'")
print(f"  Wall height: {WALL_HEIGHT}'")

# ============================================================================
# STEP 4: Create Exterior Walls Using Polyline
# ============================================================================
print("\n4. Creating exterior walls (8\" CMU)...")

# Use createWallsFromPolyline for the exterior shell
# Note: Not specifying wallTypeId - will use default Basic wall type
polyline_params = {
    "points": exterior_boundary,
    "levelId": first_floor_level_id,
    "height": WALL_HEIGHT,
    "closed": True  # This is a closed polyline
}

result = send_mcp_request("createWallsFromPolyline", polyline_params)
print_result(result, "Create Exterior Walls")

if result.get("success"):
    wall_ids = result.get("wallIds", [])
    print(f"\n  Created {len(wall_ids)} exterior walls")
    for i, wid in enumerate(wall_ids):
        print(f"    Wall {i+1}: ID {wid}")

# ============================================================================
# STEP 5: Create Interior Partition Walls
# ============================================================================
print("\n5. Creating interior partition walls...")

# Interior walls based on A-100 floor plan layout
# These are approximate positions based on room layout

interior_walls = [
    # Garage east wall (separating garage from house)
    # Format: [x, y, z] arrays - required by WallMethods.cs
    {"start": [12.0, 0, 0], "end": [12.0, 20.0, 0], "name": "Garage East Wall"},

    # Wall between Kitchen and Living Room (partial)
    {"start": [22.0, 10.0, 0], "end": [22.0, 20.0, 0], "name": "Kitchen/Living Wall"},

    # Wall between Foyer/Closet/Bath - one continuous wall from X=12 to X=22 at Y=10
    # Note: This replaces both "Foyer North Wall" and "Stairs South Wall" which overlapped
    {"start": [12.0, 10.0, 0], "end": [22.0, 10.0, 0], "name": "Foyer-Stairs North Wall"},

    # Utility room wall
    {"start": [8.0, 0, 0], "end": [8.0, 7.0, 0], "name": "Utility Room Wall"},

    # 1/2 Bath walls
    {"start": [16.0, 0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath East Wall"},
    {"start": [12.0, 6.0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath North Wall"},

    # Closet/Stairs enclosure - vertical wall at X=16 from Y=6 to Y=10
    {"start": [16.0, 6.0, 0], "end": [16.0, 10.0, 0], "name": "Closet West Wall"},

    # Pantry wall
    {"start": [8.0, 7.0, 0], "end": [12.0, 7.0, 0], "name": "Pantry North Wall"},
]

for wall_def in interior_walls:
    # Note: Not specifying wallTypeId - will use default Basic wall type
    wall_params = {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": first_floor_level_id,
        "height": WALL_HEIGHT
    }

    result = send_mcp_request("createWallByPoints", wall_params)
    if result.get("success"):
        print(f"    Created: {wall_def['name']} (ID: {result.get('wallId')})")
    else:
        print(f"    FAILED: {wall_def['name']} - {result.get('error')}")

# ============================================================================
# STEP 6: Verify Wall Creation
# ============================================================================
print("\n6. Verifying walls created...")
walls = send_mcp_request("getWalls", {})
if walls.get("success"):
    wall_list = walls.get("walls", [])
    print(f"\n  Total walls in model: {len(wall_list)}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("FIRST FLOOR WALL CREATION COMPLETE")
print("="*80)
print("\nNext steps:")
print("  1. Open 3D view in Revit to verify wall placement")
print("  2. Adjust wall positions as needed")
print("  3. Run floor creation script")
print("  4. Add doors and windows")
print("="*80 + "\n")
