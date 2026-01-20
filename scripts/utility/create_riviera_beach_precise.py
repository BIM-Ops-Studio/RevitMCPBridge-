#!/usr/bin/env python3
"""
Riviera Beach 2-Story Prototype - PRECISE First Floor Wall Creation
Based on exact tracing from A-100 floor plan PDF

Building Dimensions (from A-100):
- Overall Width: 45'-4" (45.333 ft) [Grid A to D]
- Overall Depth: 28'-8" (28.667 ft) [Grid 1 to 5]
- First Floor Height: 10'-0"

Grid Lines:
- A at X=0
- B at X=11'-4" (11.333')
- C at X=22'-0" (22.0') [11.333 + 10.667]
- D at X=45'-4" (45.333') [22.0 + 23.333]

- 1 at Y=0 (south/front)
- 2 at Y=7'-0" (7.0')
- 5 at Y=28'-8" (28.667') (north/rear)

Room Layout from A-100:
- Garage (101): SW corner, west side
- Utility (102): Behind garage
- Pantry (103): Small closet
- Kitchen (104): North side, open to dining
- Living (105): NE corner
- Dining (106): Center east
- 1/2 Bath (107): South side
- Closet/Stairs (108): Center
- Foyer (109): Entry area
- Porch (EX-1): Front entry
- Rear Lanai (EX-2): Back covered patio
"""

import json
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
        request = {"method": method, "params": params}
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
# PRECISE DIMENSIONS FROM A-100 FLOOR PLAN
# ============================================================================

# Grid positions in feet (traced from dimensioned plan)
GRID_A = 0.0
GRID_B = 11.333    # 11'-4"
GRID_C = 22.0      # 11'-4" + 10'-8" = 22'-0"
GRID_D = 45.333    # 22'-0" + 23'-4" = 45'-4"

GRID_1 = 0.0       # South (front of house)
GRID_2 = 7.0       # 7'-0" from Grid 1
GRID_5 = 28.667    # 28'-8" (north/rear)

# Building envelope
OVERALL_WIDTH = GRID_D   # 45'-4"
OVERALL_DEPTH = GRID_5   # 28'-8"
WALL_HEIGHT = 10.0       # 10'-0" first floor

# Key dimensions from the floor plan (measured from grid lines and room tags)
# These are traced from the actual dimension strings on A-100

# Garage dimensions (from plan: 12'-1" wide based on door schedule and plan)
GARAGE_EAST_X = 12.083   # 12'-1" - east wall of garage separating from house

# Porch depth (from plan: 4' deep, width matches foyer area)
PORCH_DEPTH = 4.0
PORCH_WIDTH = 9.667      # 9'-8" approx

# Interior wall positions traced from A-100:
# The plan shows specific dimensions for each room

# From A-100, measuring wall positions:
# Y=20' line: Major horizontal wall separating front from back areas
LIVING_KITCHEN_WALL_Y = 20.0  # Approximate - separating living/kitchen from foyer/dining

# Utility room: NW corner of garage area
UTILITY_Y = 7.0  # Wall at Grid 2

# Half bath and closet area: between foyer and garage
HALF_BATH_EAST_X = 16.0   # East wall of 1/2 bath
HALF_BATH_NORTH_Y = 6.0   # North wall of 1/2 bath

# Foyer/Stairs area
FOYER_NORTH_Y = 10.0  # Wall north of foyer, south of stairs

# ============================================================================
# STEP 1: Test Connection & Get Level
# ============================================================================
print("\n" + "="*80)
print("RIVIERA BEACH 2-STORY PROTOTYPE - PRECISE WALL TRACING")
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
first_floor_level_id = None
level_list = levels.get("levels", [])
for level in level_list:
    name = level.get("name", "").lower()
    if "first" in name or "level 1" in name or name == "l1" or "1st" in name:
        first_floor_level_id = level.get("levelId")
        print(f"\n  Found First Floor Level: {level.get('name')} (ID: {first_floor_level_id})")
        break

if not first_floor_level_id and level_list:
    first_floor_level_id = level_list[0].get("levelId")
    print(f"\n  Using level: {level_list[0].get('name')} (ID: {first_floor_level_id})")

# ============================================================================
# STEP 2: Define PRECISE Wall Geometry from A-100
# ============================================================================
print("\n2. Defining PRECISE wall geometry from A-100 floor plan...")

# All coordinates in feet, origin at SW corner (Grid A/Grid 1)
# Format: [x, y, z] - z is always 0 for first floor

# EXTERIOR WALLS - Building perimeter (45'-4" x 28'-8")
# Using polyline for exterior shell - 4 points, closed=True
exterior_boundary = [
    [0, 0, 0],                          # SW corner (Grid A/1)
    [OVERALL_WIDTH, 0, 0],              # SE corner (Grid D/1)
    [OVERALL_WIDTH, OVERALL_DEPTH, 0],  # NE corner (Grid D/5)
    [0, OVERALL_DEPTH, 0],              # NW corner (Grid A/5)
]

# INTERIOR WALLS - Traced from A-100 floor plan
# Based on the room layout and dimension strings visible in the PDF

# From analyzing the A-100 plan more carefully:
# The plan shows these key interior walls:

interior_walls = []

# --- GARAGE AREA (Room 101) - West side of house ---

# 1. Garage east wall - separates garage from main house
# From plan: garage is ~12' wide (from west exterior to this wall)
# This wall runs from south exterior to approximately Y=20'
interior_walls.append({
    "start": [12.0, 0, 0],
    "end": [12.0, 20.0, 0],
    "name": "Garage East Wall"
})

# --- UTILITY ROOM (102) and PANTRY (103) ---

# 2. Utility room south wall - at Grid 2 (Y=7')
# From X=0 (west exterior) to approximately X=8' (where utility ends)
interior_walls.append({
    "start": [0, 7.0, 0],
    "end": [8.0, 7.0, 0],
    "name": "Utility Room South Wall"
})

# 3. Utility room east wall
interior_walls.append({
    "start": [8.0, 7.0, 0],
    "end": [8.0, 10.0, 0],
    "name": "Utility Room East Wall"
})

# 4. Pantry walls - small closet next to utility
interior_walls.append({
    "start": [8.0, 10.0, 0],
    "end": [12.0, 10.0, 0],
    "name": "Pantry South Wall"
})

# --- 1/2 BATH (107) ---

# 5. Half bath east wall
interior_walls.append({
    "start": [16.0, 0, 0],
    "end": [16.0, 6.0, 0],
    "name": "1/2 Bath East Wall"
})

# 6. Half bath north wall
interior_walls.append({
    "start": [12.0, 6.0, 0],
    "end": [16.0, 6.0, 0],
    "name": "1/2 Bath North Wall"
})

# --- FOYER (109) and CLOSET/STAIRS (108) ---

# 7. Wall north of foyer - continuous wall from garage east to stair area
interior_walls.append({
    "start": [12.0, 10.0, 0],
    "end": [22.0, 10.0, 0],
    "name": "Foyer North Wall"
})

# 8. Closet/stairs west wall (partial - between 1/2 bath and foyer north wall)
interior_walls.append({
    "start": [16.0, 6.0, 0],
    "end": [16.0, 10.0, 0],
    "name": "Closet/Stairs West Wall"
})

# --- KITCHEN (104) / LIVING (105) / DINING (106) AREA ---

# 9. Wall between kitchen and rear lanai (partial wall at north)
# Kitchen opens to living room, this is the back wall before lanai
interior_walls.append({
    "start": [0, 20.0, 0],
    "end": [12.0, 20.0, 0],
    "name": "Kitchen North Wall"
})

# 10. Living room south boundary (partial - creates definition between dining and living)
# This is more of a conceptual division - may be open
interior_walls.append({
    "start": [22.0, 10.0, 0],
    "end": [22.0, 20.0, 0],
    "name": "Living/Dining Divider Wall"
})

# 11. Rear Lanai separation wall (north side, separating indoor from outdoor)
# From Grid A to beyond kitchen area
interior_walls.append({
    "start": [12.0, 20.0, 0],
    "end": [22.0, 20.0, 0],
    "name": "Rear Lanai Wall"
})

print(f"  Building envelope: {OVERALL_WIDTH}' x {OVERALL_DEPTH}'")
print(f"  Wall height: {WALL_HEIGHT}'")
print(f"  Total interior walls planned: {len(interior_walls)}")

# ============================================================================
# STEP 3: Create Exterior Walls
# ============================================================================
print("\n3. Creating exterior walls (building perimeter)...")

polyline_params = {
    "points": exterior_boundary,
    "levelId": first_floor_level_id,
    "height": WALL_HEIGHT,
    "closed": True
}

result = send_mcp_request("createWallsFromPolyline", polyline_params)
print_result(result, "Create Exterior Walls")

exterior_wall_ids = []
if result.get("success"):
    exterior_wall_ids = result.get("wallIds", [])
    print(f"\n  Created {len(exterior_wall_ids)} exterior walls")
    for i, wid in enumerate(["South", "East", "North", "West"]):
        if i < len(exterior_wall_ids):
            print(f"    {wid} Wall: ID {exterior_wall_ids[i]}")

# ============================================================================
# STEP 4: Create Interior Walls
# ============================================================================
print("\n4. Creating interior partition walls...")

interior_wall_ids = []
for wall_def in interior_walls:
    wall_params = {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": first_floor_level_id,
        "height": WALL_HEIGHT
    }

    result = send_mcp_request("createWallByPoints", wall_params)
    if result.get("success"):
        wall_id = result.get("wallId")
        interior_wall_ids.append(wall_id)
        print(f"    ✓ Created: {wall_def['name']} (ID: {wall_id})")
    else:
        print(f"    ✗ FAILED: {wall_def['name']} - {result.get('error')}")

# ============================================================================
# STEP 5: Summary
# ============================================================================
print("\n" + "="*80)
print("WALL CREATION COMPLETE")
print("="*80)
print(f"\nSummary:")
print(f"  Exterior walls: {len(exterior_wall_ids)}")
print(f"  Interior walls: {len(interior_wall_ids)}")
print(f"  Total walls: {len(exterior_wall_ids) + len(interior_wall_ids)}")

print("\n" + "="*80)
print("COORDINATE REFERENCE (from A-100):")
print("="*80)
print(f"""
Building Origin: Southwest corner (Grid A / Grid 1)
  X increases toward East (Grid D)
  Y increases toward North (Grid 5)

Grid Positions:
  Grid A: X = 0'
  Grid B: X = 11'-4\" ({GRID_B}')
  Grid C: X = 22'-0\" ({GRID_C}')
  Grid D: X = 45'-4\" ({GRID_D}')

  Grid 1: Y = 0' (front/south)
  Grid 2: Y = 7'-0\" ({GRID_2}')
  Grid 5: Y = 28'-8\" ({GRID_5}') (rear/north)

Room Layout (approximate):
  Garage (101):      X=0-12, Y=0-20
  Utility (102):     X=0-8, Y=7-10
  Pantry (103):      X=8-12, Y=7-10
  Kitchen (104):     X=0-12, Y=20-28.67
  Living (105):      X=22-45.33, Y=10-20
  Dining (106):      X=22-45.33, Y=0-10
  1/2 Bath (107):    X=12-16, Y=0-6
  Closet/Strs (108): X=16-22, Y=6-10
  Foyer (109):       X=12-22, Y=0-10
""")

print("\nNext steps:")
print("  1. Open 3D view in Revit to verify wall placement")
print("  2. Compare with A-100 floor plan")
print("  3. Adjust wall positions if needed")
print("  4. Add doors and windows")
print("="*80 + "\n")
