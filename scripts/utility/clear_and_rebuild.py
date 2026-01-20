#!/usr/bin/env python3
"""
Clear existing walls and rebuild with precise coordinates from A-100
This script combines deletion and recreation in one workflow.
"""

import json
import sys
import time

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

        # Read response with larger buffer
        response_data = b""
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            try:
                decoded = response_data.decode('utf-8').strip()
                if decoded.endswith('}') or decoded.endswith(']'):
                    json.loads(decoded)  # Validate complete JSON
                    break
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            if len(chunk) < 64 * 1024:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8'))
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running"}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# STEP 1: Test Connection
# ============================================================================
print("\n" + "="*80)
print("RIVIERA BEACH - CLEAR AND REBUILD WALLS")
print("="*80)

print("\n1. Testing MCP connection...")
result = send_mcp_request("getLevels", {})
if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    print("   Please start the MCP server in Revit.")
    sys.exit(1)

print("   Connected to Revit!")

# Get first floor level
first_floor_level_id = None
for level in result.get("levels", []):
    name = level.get("name", "").lower()
    if "first" in name or "level 1" in name or name == "l1":
        first_floor_level_id = level.get("levelId")
        print(f"   Found level: {level.get('name')} (ID: {first_floor_level_id})")
        break

if not first_floor_level_id:
    first_floor_level_id = result.get("levels", [{}])[0].get("levelId")
    print(f"   Using first level (ID: {first_floor_level_id})")

# ============================================================================
# STEP 2: Get and Delete Existing Walls
# ============================================================================
print("\n2. Querying existing walls...")
walls_result = send_mcp_request("getWalls", {})

if walls_result.get("success"):
    existing_walls = walls_result.get("walls", [])
    print(f"   Found {len(existing_walls)} existing walls")

    if existing_walls:
        print("\n3. Deleting existing walls...")
        deleted = 0
        failed = 0
        for wall in existing_walls:
            wall_id = wall.get("wallId")
            del_result = send_mcp_request("deleteWall", {"wallId": wall_id})
            if del_result.get("success"):
                deleted += 1
                print(f"   [OK] Deleted wall {wall_id}")
            else:
                failed += 1
                print(f"   [FAIL] Delete {wall_id}: {del_result.get('error')}")

        print(f"\n   Deleted: {deleted}, Failed: {failed}")
        time.sleep(0.5)  # Brief pause to let Revit process
else:
    print(f"   Warning: Could not query walls: {walls_result.get('error')}")

# ============================================================================
# STEP 3: Create New Walls with PRECISE Coordinates
# ============================================================================
print("\n4. Creating precise walls from A-100 floor plan...")

# Dimensions from A-100
OVERALL_WIDTH = 45.333   # 45'-4"
OVERALL_DEPTH = 28.667   # 28'-8"
WALL_HEIGHT = 10.0       # 10'-0"

# Grid positions
GRID_A = 0.0
GRID_B = 11.333
GRID_C = 22.0
GRID_D = 45.333
GRID_1 = 0.0
GRID_2 = 7.0
GRID_5 = 28.667

# Exterior boundary (closed polyline)
exterior_boundary = [
    [0, 0, 0],
    [OVERALL_WIDTH, 0, 0],
    [OVERALL_WIDTH, OVERALL_DEPTH, 0],
    [0, OVERALL_DEPTH, 0],
]

print("   Creating exterior walls...")
result = send_mcp_request("createWallsFromPolyline", {
    "points": exterior_boundary,
    "levelId": first_floor_level_id,
    "height": WALL_HEIGHT,
    "closed": True
})

if result.get("success"):
    ext_ids = result.get("wallIds", [])
    print(f"   [OK] Created {len(ext_ids)} exterior walls")
else:
    print(f"   [FAIL] {result.get('error')}")

# Interior walls - traced from A-100
interior_walls = [
    # Garage east wall
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

print("\n   Creating interior walls...")
created = 0
for wall_def in interior_walls:
    result = send_mcp_request("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": first_floor_level_id,
        "height": WALL_HEIGHT
    })
    if result.get("success"):
        created += 1
        print(f"   [OK] {wall_def['name']}")
    else:
        print(f"   [FAIL] {wall_def['name']}: {result.get('error')}")

print(f"\n   Created {created}/{len(interior_walls)} interior walls")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print("""
The walls have been created based on the A-100 floor plan.

Please open a 3D view in Revit to verify the layout matches the PDF.

Room Layout (SW corner = origin):
┌──────────────────────────────────────────────┐ Y=28.67'
│              REAR LANAI (EX-2)               │
├──────────┬───────────┬───────────────────────┤ Y=20'
│ KITCHEN  │           │                       │
│   104    │           │     LIVING RM 105     │
├────┬─────┤           │                       │
│UTIL│PNTR │           │                       │
│102 │103  │           ├───────────────────────┤ Y=10'
├────┴─────┼─────┬─────┤                       │
│          │CLST │     │     DINING RM 106     │
│  GARAGE  │108  │     │                       │
│   101    ├─────┼─────┤                       │
│          │1/2BA│FOYER│                       │
│          │107  │109  │                       │
└──────────┴─────┴─────┴───────────────────────┘ Y=0'
X=0       X=12  X=16  X=22                   X=45.33'

Compare this with sheet A-100 in the PDF to verify accuracy.
""")
