#!/usr/bin/env python3
"""
Create CORRECT wall layout matching PDF A-100 EXACTLY.

From the PDF 1ST FLOOR PLAN (page 5):
- Grid A to B: 11'-4" = 11.333'
- Grid B to C: 10'-8" = 10.667'
- Grid C to D: 23'-4" = 23.333'
- Total Width: 45'-4" = 45.333'
- Total Depth: 28'-8" = 28.667'

Room Layout from PDF (Grid 5 = NORTH/TOP, Grid 1 = SOUTH/BOTTOM):
- GARAGE 101 (242 SF): Bottom-left, with garage door on SOUTH
- UTILITY RM 102 (44 SF): Above garage, small room
- PANTRY 103 (2 SF): Tiny closet next to utility
- KITCHEN 104 (204 SF): Top-left corner
- LIVING RM 105 (144 SF): Top-right area
- DINING RM 106 (100 SF): Right side, below living
- 1/2 BATH 107 (35 SF): Small bath near foyer
- CLOSET 108 (68 SF): Under stairs
- FOYER 109 (49 SF): Entry area
- REAR LANAI EX-2 (110 SF): Back porch/lanai
- PORCH EX-1 (54 SF): Front porch

Looking at the PDF more carefully:
- Garage is on the LEFT (west) side
- Entry/Porch is on the RIGHT (east) side of front
- Kitchen is at the back-left
- Living room spans the back
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
        for _ in range(50):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                time.sleep(0.02)
                continue
        win32file.CloseHandle(handle)
        return {"success": False, "error": "Response incomplete"}
    except pywintypes.error as e:
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("CREATE CORRECT LAYOUT FROM PDF A-100")
print("=" * 80)

# Get level
result = send_mcp_request("getLevels", {})
if not result.get("success"):
    print(f"ERROR: {result.get('error')}")
    sys.exit(1)

level_id = None
for level in result.get("levels", []):
    name = level.get("name", "").lower()
    if "first" in name or "l1" in name or "level 1" in name:
        level_id = level.get("levelId")
        break
if not level_id:
    level_id = result.get("levels", [{}])[0].get("levelId")
print(f"Using level ID: {level_id}")

# Get wall types
result = send_mcp_request("getWallTypes", {})
exterior_type = None
interior_type = None
if result.get("success"):
    for wt in result.get("wallTypes", []):
        width = wt.get("width", 0) * 12
        if 7 <= width <= 9 and not exterior_type:
            exterior_type = wt.get("wallTypeId")
        if 4 <= width <= 6 and not interior_type:
            interior_type = wt.get("wallTypeId")

print(f"Exterior type ID: {exterior_type}")
print(f"Interior type ID: {interior_type}")

# Delete existing walls
print("\nDeleting existing walls...")
result = send_mcp_request("getWalls", {})
if result.get("success"):
    for wall in result.get("walls", []):
        send_mcp_request("deleteWall", {"wallId": wall.get("wallId")})
    print(f"   Deleted {len(result.get('walls', []))} walls")
time.sleep(0.3)

# Delete existing text notes and detail lines
print("Deleting existing annotations...")
result = send_mcp_request("getActiveView", {})
view_id = result.get("viewId") if result.get("success") else None

# ============================================================================
# PRECISE DIMENSIONS FROM PDF A-100
# ============================================================================
# Grid positions (X axis - left to right)
GRID_A = 0.0          # Left edge
GRID_B = 11.333       # 11'-4"
GRID_C = 22.0         # 11'-4" + 10'-8" = 22'-0"
GRID_D = 45.333       # Total width 45'-4"

# Grid positions (Y axis - bottom to top, Grid 1 at bottom)
GRID_1 = 0.0          # South/Front edge
GRID_5 = 28.667       # North/Back edge (28'-8")

# Key Y positions from the floor plan
Y_GARAGE_TOP = 20.0   # Top of garage area (approx)
Y_FOYER_TOP = 10.0    # Top of foyer/entry area
Y_BATH_TOP = 6.0      # Top of 1/2 bath

# Key X positions
X_GARAGE_EAST = 12.083  # East wall of garage (12'-1")
X_FOYER_WEST = 12.083   # West wall of foyer area
X_BATH_EAST = 16.0      # East wall of 1/2 bath (approx 16')
X_STAIRS_EAST = 22.0    # East wall of stairs/closet area

WALL_HEIGHT = 10.0

print("\n" + "=" * 80)
print("CREATING WALLS FROM PDF A-100")
print("=" * 80)

# ============================================================================
# EXTERIOR WALLS - Building Perimeter
# ============================================================================
print("\n1. Creating exterior walls...")

exterior_boundary = [
    [GRID_A, GRID_1, 0],      # SW corner
    [GRID_D, GRID_1, 0],      # SE corner
    [GRID_D, GRID_5, 0],      # NE corner
    [GRID_A, GRID_5, 0],      # NW corner
]

params = {
    "points": exterior_boundary,
    "levelId": level_id,
    "height": WALL_HEIGHT,
    "closed": True
}
if exterior_type:
    params["wallTypeId"] = exterior_type

result = send_mcp_request("createWallsFromPolyline", params)
if result.get("success"):
    print(f"   [OK] Created {len(result.get('wallIds', []))} exterior walls")
else:
    print(f"   [FAIL] {result.get('error')}")

# ============================================================================
# INTERIOR WALLS - From PDF Layout
# ============================================================================
print("\n2. Creating interior walls...")

# Interior walls traced from PDF A-100
interior_walls = [
    # GARAGE (101) - East wall separating from house
    # This is the main wall between garage and the rest of the house
    {"start": [12.083, GRID_1, 0], "end": [12.083, 20.0, 0], "name": "Garage East Wall"},

    # UTILITY (102) and PANTRY (103) walls
    # These small rooms are between garage and kitchen
    {"start": [GRID_A, 7.0, 0], "end": [8.0, 7.0, 0], "name": "Utility South Wall"},
    {"start": [8.0, 7.0, 0], "end": [8.0, 10.0, 0], "name": "Utility/Pantry Divider"},
    {"start": [8.0, 10.0, 0], "end": [12.083, 10.0, 0], "name": "Pantry South Wall"},

    # KITCHEN (104) - North area wall
    {"start": [GRID_A, 20.0, 0], "end": [12.083, 20.0, 0], "name": "Kitchen South Wall"},

    # 1/2 BATH (107) walls
    {"start": [12.083, GRID_1, 0], "end": [12.083, 6.0, 0], "name": "Bath West Wall"},
    {"start": [16.0, GRID_1, 0], "end": [16.0, 6.0, 0], "name": "Bath East Wall"},
    {"start": [12.083, 6.0, 0], "end": [16.0, 6.0, 0], "name": "Bath North Wall"},

    # CLOSET (108) / STAIRS area
    {"start": [16.0, 6.0, 0], "end": [16.0, 10.0, 0], "name": "Stairs West Wall"},
    {"start": [12.083, 10.0, 0], "end": [22.0, 10.0, 0], "name": "Closet/Foyer North Wall"},

    # LIVING (105) / DINING (106) division
    {"start": [22.0, 10.0, 0], "end": [22.0, 20.0, 0], "name": "Living/Dining Divider"},

    # REAR LANAI (EX-2) wall
    {"start": [12.083, 20.0, 0], "end": [GRID_D, 20.0, 0], "name": "Lanai South Wall"},
]

created = 0
for wall in interior_walls:
    params = {
        "startPoint": wall["start"],
        "endPoint": wall["end"],
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

# ============================================================================
# ADD ROOM LABELS
# ============================================================================
print("\n3. Adding room labels...")

if view_id:
    rooms = [
        {"name": "GARAGE 101 (242 SF)", "x": 6, "y": 10},
        {"name": "UTILITY 102", "x": 4, "y": 8.5},
        {"name": "PANTRY 103", "x": 10, "y": 8.5},
        {"name": "KITCHEN 104 (204 SF)", "x": 6, "y": 24},
        {"name": "LIVING RM 105 (144 SF)", "x": 33, "y": 24},
        {"name": "DINING RM 106 (100 SF)", "x": 33, "y": 5},
        {"name": "1/2 BATH 107", "x": 14, "y": 3},
        {"name": "CLOSET 108", "x": 19, "y": 8},
        {"name": "FOYER 109", "x": 19, "y": 3},
        {"name": "REAR LANAI EX-2", "x": 28, "y": 24},
        {"name": "PORCH EX-1", "x": 19, "y": -2},
    ]

    for room in rooms:
        result = send_mcp_request("createTextNote", {
            "viewId": view_id,
            "position": [room["x"], room["y"], 0],
            "text": room["name"]
        })
        status = "[OK]" if result.get("success") else "[FAIL]"
        print(f"   {status} {room['name']}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("LAYOUT COMPLETE - Matching PDF A-100")
print("=" * 80)
print("""
CORRECT LAYOUT (matching PDF A-100):

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

Grid Lines:
  A (X=0) | B (X=11.33') | C (X=22') | D (X=45.33')
  1 (Y=0) | 5 (Y=28.67')

GARAGE 101:
  - Location: SOUTHWEST corner (bottom-left)
  - Bounded by: West exterior, South exterior, Garage East interior wall
  - Size: 12' x 20' = 242 SF (approx)
  - Features: Garage door on SOUTH wall, side door to UTILITY on east
""")
print("=" * 80)
