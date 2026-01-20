#!/usr/bin/env python3
"""
Delete all walls and trace new walls based on the PDF visible in Revit.
The PDF is positioned in Revit - we need to place walls to match it.
"""

import json
import sys
import time

try:
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, params):
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

        response_data = b""
        for _ in range(100):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                time.sleep(0.05)
                continue
        win32file.CloseHandle(handle)
        return {"success": False, "error": "Response incomplete"}
    except pywintypes.error as e:
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("STEP 1: DELETE ALL EXISTING WALLS")
print("=" * 80)

result = send_mcp_request("getWalls", {})
if result.get("success"):
    walls = result.get("walls", [])
    print(f"Found {len(walls)} walls to delete")
    for wall in walls:
        wid = wall.get("wallId")
        r = send_mcp_request("deleteWall", {"wallId": wid})
        status = "[OK]" if r.get("success") else "[FAIL]"
        print(f"  {status} Wall {wid}")
    time.sleep(0.5)

    # Verify
    result = send_mcp_request("getWalls", {})
    remaining = len(result.get("walls", []))
    print(f"\nAfter deletion: {remaining} walls remain")
else:
    print(f"Error getting walls: {result.get('error')}")

print("\n" + "=" * 80)
print("STEP 2: GET LEVEL AND WALL TYPES")
print("=" * 80)

# Get level
result = send_mcp_request("getLevels", {})
level_id = None
if result.get("success"):
    for level in result.get("levels", []):
        name = level.get("name", "").lower()
        if "l1" in name or "first" in name or "level 1" in name:
            level_id = level.get("levelId")
            print(f"Using level: {level.get('name')} (ID: {level_id})")
            break
    if not level_id and result.get("levels"):
        level_id = result.get("levels")[0].get("levelId")
        print(f"Using first level: {result.get('levels')[0].get('name')} (ID: {level_id})")

# Get wall types
result = send_mcp_request("getWallTypes", {})
exterior_type = None
interior_type = None
if result.get("success"):
    for wt in result.get("wallTypes", []):
        width = wt.get("width", 0) * 12  # Convert to inches
        name = wt.get("name", "").lower()
        if 7 <= width <= 9 and not exterior_type:
            exterior_type = wt.get("wallTypeId")
            print(f"Exterior wall type: {wt.get('name')} (ID: {exterior_type}, width: {width}\")")
        if 4 <= width <= 6 and not interior_type:
            interior_type = wt.get("wallTypeId")
            print(f"Interior wall type: {wt.get('name')} (ID: {interior_type}, width: {width}\")")

WALL_HEIGHT = 10.0

print("\n" + "=" * 80)
print("STEP 3: CREATE WALLS MATCHING PDF A-100")
print("=" * 80)

# ============================================================================
# Looking at the PDF in the Revit view, I can see:
# - The PDF is positioned with its lower-left corner near the Revit origin
# - Grid A is at the LEFT (west side)
# - Grid D is at the RIGHT (east side)
# - Grid 1 is at the BOTTOM (south side)
# - Grid 5 is at the TOP (north side)
#
# From the PDF dimensions:
# - A to B: 11'-4" = 11.333'
# - B to C: 10'-8" = 10.667'
# - C to D: 23'-4" = 23.333'
# - Total width: 45'-4" = 45.333'
# - Total depth: 28'-8" = 28.667'
#
# The PDF appears to be placed at approximately (0,0) in Revit
# ============================================================================

# Based on PDF A-100 1ST FLOOR PLAN (page 5):
# Grid positions
GRID_A = 0.0
GRID_B = 11.333   # 11'-4"
GRID_C = 22.0     # 11'-4" + 10'-8"
GRID_D = 45.333   # Total width

GRID_1 = 0.0      # South edge
GRID_5 = 28.667   # North edge (28'-8")

# Key Y positions from floor plan
Y_GARAGE_NORTH = 20.0    # North wall of garage
Y_UTILITY_SOUTH = 7.0    # South wall of utility
Y_BATH_NORTH = 6.0       # North wall of 1/2 bath
Y_CLOSET_NORTH = 10.0    # North wall of closet/stairs area
Y_LANAI_SOUTH = 20.0     # South edge of rear lanai

# Key X positions
X_GARAGE_EAST = 12.083   # East wall of garage (12'-1")
X_UTILITY_EAST = 8.0     # East wall of utility
X_BATH_EAST = 16.0       # East wall of 1/2 bath
X_STAIRS_EAST = 22.0     # East wall of stairs/closet

print("\n1. Creating EXTERIOR WALLS (building perimeter)...")

# Exterior perimeter - simple rectangle for now
exterior_walls = [
    {"start": [GRID_A, GRID_1], "end": [GRID_D, GRID_1], "name": "South Exterior"},
    {"start": [GRID_D, GRID_1], "end": [GRID_D, GRID_5], "name": "East Exterior"},
    {"start": [GRID_D, GRID_5], "end": [GRID_A, GRID_5], "name": "North Exterior"},
    {"start": [GRID_A, GRID_5], "end": [GRID_A, GRID_1], "name": "West Exterior"},
]

for wall in exterior_walls:
    params = {
        "startPoint": wall["start"] + [0],
        "endPoint": wall["end"] + [0],
        "levelId": level_id,
        "height": WALL_HEIGHT
    }
    if exterior_type:
        params["wallTypeId"] = exterior_type

    result = send_mcp_request("createWallByPoints", params)
    status = "[OK]" if result.get("success") else "[FAIL]"
    print(f"   {status} {wall['name']}: ({wall['start'][0]:.1f}, {wall['start'][1]:.1f}) to ({wall['end'][0]:.1f}, {wall['end'][1]:.1f})")

print("\n2. Creating INTERIOR WALLS...")

# Interior walls traced from PDF A-100
interior_walls = [
    # GARAGE east wall - separates garage from house
    {"start": [X_GARAGE_EAST, GRID_1], "end": [X_GARAGE_EAST, Y_GARAGE_NORTH], "name": "Garage East"},

    # UTILITY room walls
    {"start": [GRID_A, Y_UTILITY_SOUTH], "end": [X_UTILITY_EAST, Y_UTILITY_SOUTH], "name": "Utility South"},
    {"start": [X_UTILITY_EAST, Y_UTILITY_SOUTH], "end": [X_UTILITY_EAST, Y_CLOSET_NORTH], "name": "Utility/Pantry Divider"},
    {"start": [X_UTILITY_EAST, Y_CLOSET_NORTH], "end": [X_GARAGE_EAST, Y_CLOSET_NORTH], "name": "Pantry South"},

    # KITCHEN south wall (separates kitchen from utility area)
    {"start": [GRID_A, Y_GARAGE_NORTH], "end": [X_GARAGE_EAST, Y_GARAGE_NORTH], "name": "Kitchen South"},

    # 1/2 BATH walls
    {"start": [X_BATH_EAST, GRID_1], "end": [X_BATH_EAST, Y_BATH_NORTH], "name": "Bath East"},
    {"start": [X_GARAGE_EAST, Y_BATH_NORTH], "end": [X_BATH_EAST, Y_BATH_NORTH], "name": "Bath North"},

    # STAIRS/CLOSET area
    {"start": [X_BATH_EAST, Y_BATH_NORTH], "end": [X_BATH_EAST, Y_CLOSET_NORTH], "name": "Stairs West"},
    {"start": [X_GARAGE_EAST, Y_CLOSET_NORTH], "end": [X_STAIRS_EAST, Y_CLOSET_NORTH], "name": "Foyer/Closet North"},

    # LIVING/DINING divider
    {"start": [X_STAIRS_EAST, Y_CLOSET_NORTH], "end": [X_STAIRS_EAST, Y_LANAI_SOUTH], "name": "Living/Dining Divider"},

    # REAR LANAI south wall
    {"start": [X_GARAGE_EAST, Y_LANAI_SOUTH], "end": [GRID_D, Y_LANAI_SOUTH], "name": "Lanai South"},
]

created = 0
for wall in interior_walls:
    params = {
        "startPoint": wall["start"] + [0],
        "endPoint": wall["end"] + [0],
        "levelId": level_id,
        "height": WALL_HEIGHT
    }
    if interior_type:
        params["wallTypeId"] = interior_type

    result = send_mcp_request("createWallByPoints", params)
    if result.get("success"):
        created += 1
        print(f"   [OK] {wall['name']}")
    else:
        print(f"   [FAIL] {wall['name']}: {result.get('error')}")

print(f"\n   Created {created}/{len(interior_walls)} interior walls")

print("\n" + "=" * 80)
print("STEP 4: VERIFY WALLS")
print("=" * 80)

result = send_mcp_request("getWalls", {})
if result.get("success"):
    walls = result.get("walls", [])
    print(f"Total walls in model: {len(walls)}")

    # Calculate bounding box
    all_x = []
    all_y = []
    for wall in walls:
        start = wall.get("startPoint", {})
        end = wall.get("endPoint", {})
        if isinstance(start, dict):
            all_x.extend([start.get("x", 0), end.get("x", 0)])
            all_y.extend([start.get("y", 0), end.get("y", 0)])

    if all_x and all_y:
        print(f"\nBounding box:")
        print(f"   X: {min(all_x):.2f}' to {max(all_x):.2f}' (width: {max(all_x)-min(all_x):.2f}')")
        print(f"   Y: {min(all_y):.2f}' to {max(all_y):.2f}' (depth: {max(all_y)-min(all_y):.2f}')")
        print(f"\nExpected from PDF:")
        print(f"   Width: 45.33' | Actual: {max(all_x)-min(all_x):.2f}'")
        print(f"   Depth: 28.67' | Actual: {max(all_y)-min(all_y):.2f}'")

print("\n" + "=" * 80)
print("LAYOUT DIAGRAM (What should be in Revit)")
print("=" * 80)
print("""
                    NORTH (Y = 28.67')
    +------------------------------------------+
    |  KITCHEN 104  |     REAR LANAI EX-2      |
    |    204 SF     |       110 SF             |
    +------+--------+                          |
    | UTIL | PANTRY |     LIVING RM 105        |
    | 102  |  103   |       144 SF             |
    +------+--------+--------------------------+
    |              |                           |
    |   GARAGE     |     DINING RM 106         |
    |     101      |       100 SF              |
    |   242 SF     +--------+------------------+
    |              | CLOSET |                  |
    |              |  108   |                  |
    |              +----+---+   FOYER 109      |
    |              |1/2 |                      |
    |              |BATH|      49 SF           |
    |              |107 |                      |
    +--------------+----+----------------------+
                    SOUTH (Y = 0)
    X=0         X=12  X=16 X=22            X=45.33'
""")
print("=" * 80)
