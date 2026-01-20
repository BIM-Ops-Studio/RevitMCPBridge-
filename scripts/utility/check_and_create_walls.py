#!/usr/bin/env python3
"""
Create walls with correct wall types for Riviera Beach 2-Story Prototype.

From PDF A-100 Wall Types:
- W1: Exterior 8" CMU + insulation + furring + GWB + stucco (~10-11" total)
- W2: Interior Load Bearing 2x4 wood stud + GWB both sides (~4-5" total)
- W3: Interior Non-Bearing 3-5/8" metal stud + GWB (~4-5" total)

This script will:
1. Query wall types one at a time to find appropriate matches
2. Clear existing walls
3. Create new walls with correct types
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
    """Send MCP request - handles large responses by reading until complete"""
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

        # Read response - keep reading until we get complete JSON
        response_data = b""
        max_attempts = 50
        for attempt in range(max_attempts):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk

                # Try to parse
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                # May need more data or just incomplete
                time.sleep(0.02)
                continue
            except Exception:
                time.sleep(0.02)
                continue

        win32file.CloseHandle(handle)
        return {"success": False, "error": f"Response incomplete: {len(response_data)} bytes"}
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running"}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("RIVIERA BEACH - CREATE WALLS WITH CORRECT TYPES")
print("=" * 80)

# ============================================================================
# STEP 1: Test Connection
# ============================================================================
print("\n1. Testing connection...")
result = send_mcp_request("getLevels", {})
if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    sys.exit(1)
print("   Connected!")

# Get first floor level
first_floor_level_id = None
for level in result.get("levels", []):
    name = level.get("name", "").lower()
    if "first" in name or "level 1" in name or name == "l1":
        first_floor_level_id = level.get("levelId")
        print(f"   Level: {level.get('name')} (ID: {first_floor_level_id})")
        break

if not first_floor_level_id:
    first_floor_level_id = result.get("levels", [{}])[0].get("levelId")
    print(f"   Using first available level (ID: {first_floor_level_id})")

# ============================================================================
# STEP 2: Find Wall Types
# ============================================================================
print("\n2. Looking for wall types...")

# Try to get wall types
result = send_mcp_request("getWallTypes", {})

exterior_type_id = None
interior_type_id = None

if result.get("success"):
    wall_types = result.get("wallTypes", [])
    print(f"   Found {len(wall_types)} wall types")

    # Look for exterior wall type (8-12" thickness)
    for wt in wall_types:
        width_inches = wt.get("width", 0) * 12
        name = wt.get("name", "").lower()

        # Prefer CMU or exterior type for exterior walls
        if 8 <= width_inches <= 12:
            if "cmu" in name or "exterior" in name or "8" in name:
                exterior_type_id = wt.get("wallTypeId")
                print(f"   Exterior candidate: {wt.get('name')} ({width_inches:.2f}\" = ID {exterior_type_id})")
                break
            elif exterior_type_id is None:
                exterior_type_id = wt.get("wallTypeId")
                print(f"   Exterior fallback: {wt.get('name')} ({width_inches:.2f}\" = ID {exterior_type_id})")

    # Look for interior wall type (4-6" thickness)
    for wt in wall_types:
        width_inches = wt.get("width", 0) * 12
        name = wt.get("name", "").lower()

        if 4 <= width_inches <= 6:
            if "interior" in name or "partition" in name or "stud" in name:
                interior_type_id = wt.get("wallTypeId")
                print(f"   Interior candidate: {wt.get('name')} ({width_inches:.2f}\" = ID {interior_type_id})")
                break
            elif interior_type_id is None:
                interior_type_id = wt.get("wallTypeId")
                print(f"   Interior fallback: {wt.get('name')} ({width_inches:.2f}\" = ID {interior_type_id})")

    # If no suitable types found, list all available
    if exterior_type_id is None or interior_type_id is None:
        print("\n   Available wall types by width:")
        for wt in sorted(wall_types, key=lambda x: x.get("width", 0)):
            width_inches = wt.get("width", 0) * 12
            print(f"     ID {wt.get('wallTypeId'):>7}: {width_inches:>6.2f}\" - {wt.get('name')}")
else:
    print(f"   WARNING: Could not query wall types: {result.get('error')}")
    print("   Will use default wall types")

# ============================================================================
# STEP 3: Delete Existing Walls
# ============================================================================
print("\n3. Deleting existing walls...")

# First try to get existing walls
walls_result = send_mcp_request("getWalls", {})
if walls_result.get("success"):
    walls = walls_result.get("walls", [])
    print(f"   Found {len(walls)} existing walls")

    for wall in walls:
        wall_id = wall.get("wallId")
        del_result = send_mcp_request("deleteWall", {"wallId": wall_id})
        if del_result.get("success"):
            print(f"   [OK] Deleted wall {wall_id}")
        else:
            print(f"   [FAIL] Wall {wall_id}: {del_result.get('error')}")

    time.sleep(0.5)  # Let Revit settle
else:
    print(f"   Could not query walls: {walls_result.get('error')}")
    print("   Continuing with wall creation...")

# ============================================================================
# STEP 4: Building Dimensions from A-100
# ============================================================================
print("\n4. Setting up building geometry from A-100...")

# Overall dimensions from PDF
OVERALL_WIDTH = 45.333   # 45'-4"
OVERALL_DEPTH = 28.667   # 28'-8"
WALL_HEIGHT = 10.0       # 10'-0"

# Grid positions (traced from A-100)
GRID_A = 0.0        # West edge
GRID_B = 11.333     # 11'-4" from A
GRID_C = 22.0       # 22'-0" from A
GRID_D = 45.333     # 45'-4" = east edge

GRID_1 = 0.0        # South edge (front)
GRID_5 = 28.667     # North edge (rear)

print(f"   Building: {OVERALL_WIDTH}' x {OVERALL_DEPTH}' x {WALL_HEIGHT}' high")
print(f"   Grid A (west): X={GRID_A}")
print(f"   Grid B: X={GRID_B}")
print(f"   Grid C: X={GRID_C}")
print(f"   Grid D (east): X={GRID_D}")

# ============================================================================
# STEP 5: Create Exterior Walls
# ============================================================================
print("\n5. Creating exterior walls...")

exterior_boundary = [
    [0, 0, 0],                          # SW corner
    [OVERALL_WIDTH, 0, 0],              # SE corner
    [OVERALL_WIDTH, OVERALL_DEPTH, 0],  # NE corner
    [0, OVERALL_DEPTH, 0],              # NW corner
]

params = {
    "points": exterior_boundary,
    "levelId": first_floor_level_id,
    "height": WALL_HEIGHT,
    "closed": True
}

if exterior_type_id:
    params["wallTypeId"] = exterior_type_id

result = send_mcp_request("createWallsFromPolyline", params)
if result.get("success"):
    ext_wall_ids = result.get("wallIds", [])
    print(f"   [OK] Created {len(ext_wall_ids)} exterior walls")
    for i, label in enumerate(["South", "East", "North", "West"]):
        if i < len(ext_wall_ids):
            print(f"       {label}: ID {ext_wall_ids[i]}")
else:
    print(f"   [FAIL] {result.get('error')}")
    ext_wall_ids = []

# ============================================================================
# STEP 6: Create Interior Walls
# ============================================================================
print("\n6. Creating interior walls...")

# Interior walls from A-100 floor plan
# Using interior wall type for all partitions
interior_walls = [
    # Garage east wall - separates garage from house
    {"start": [12.0, 0, 0], "end": [12.0, 20.0, 0], "name": "Garage East Wall"},

    # Utility room walls
    {"start": [0, 7.0, 0], "end": [8.0, 7.0, 0], "name": "Utility Room South Wall"},
    {"start": [8.0, 7.0, 0], "end": [8.0, 10.0, 0], "name": "Utility Room East Wall"},

    # Pantry south wall
    {"start": [8.0, 10.0, 0], "end": [12.0, 10.0, 0], "name": "Pantry South Wall"},

    # 1/2 Bath walls
    {"start": [16.0, 0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath East Wall"},
    {"start": [12.0, 6.0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath North Wall"},

    # Foyer/Stairs area
    {"start": [12.0, 10.0, 0], "end": [22.0, 10.0, 0], "name": "Foyer North Wall"},
    {"start": [16.0, 6.0, 0], "end": [16.0, 10.0, 0], "name": "Closet/Stairs West Wall"},

    # Kitchen/Living/Dining separation
    {"start": [0, 20.0, 0], "end": [12.0, 20.0, 0], "name": "Kitchen North Wall"},
    {"start": [22.0, 10.0, 0], "end": [22.0, 20.0, 0], "name": "Living/Dining Divider"},
    {"start": [12.0, 20.0, 0], "end": [22.0, 20.0, 0], "name": "Rear Lanai Wall"},
]

created_count = 0
failed_count = 0

for wall_def in interior_walls:
    params = {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": first_floor_level_id,
        "height": WALL_HEIGHT
    }

    if interior_type_id:
        params["wallTypeId"] = interior_type_id

    result = send_mcp_request("createWallByPoints", params)

    if result.get("success"):
        created_count += 1
        wall_type = result.get("wallType", "default")
        print(f"   [OK] {wall_def['name']} (ID: {result.get('wallId')}, Type: {wall_type})")
    else:
        failed_count += 1
        print(f"   [FAIL] {wall_def['name']}: {result.get('error')}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"   Exterior walls: {len(ext_wall_ids)}")
print(f"   Interior walls: {created_count} created, {failed_count} failed")
print(f"   Total: {len(ext_wall_ids) + created_count} walls")

if exterior_type_id:
    print(f"   Exterior wall type ID: {exterior_type_id}")
if interior_type_id:
    print(f"   Interior wall type ID: {interior_type_id}")

print("\n" + "=" * 80)
print("LAYOUT (from A-100):")
print("=" * 80)
print("""
Room Layout (SW corner = origin):

        REAR LANAI (EX-2)
        Y=28.67' ────────────────────────────────────────────
                |              REAR LANAI                    |
        Y=20'   ├──────────┬─────────────────────────────────┤
                | KITCHEN  |                                 |
                |   104    |        LIVING RM 105            |
                ├────┬─────┤                                 |
                |UTIL|PNTR |                                 |
        Y=10'   │102 │103  ├─────────────────────────────────┤
                ├────┴─────┤      │                          |
                |          │STAIRS│      DINING RM 106       |
                |  GARAGE  │  108 │                          |
        Y=6'    │   101    ├──────┤                          |
                |          │1/2 BA│       FOYER 109          |
                |          │ 107  │                          |
        Y=0'    └──────────┴──────┴──────────────────────────┘
                X=0      X=12   X=16  X=22               X=45.33'

Grid Lines:
  A (X=0) | B (X=11.33') | C (X=22') | D (X=45.33')

Compare with PDF A-100 to verify accuracy.
""")
