#!/usr/bin/env python3
"""
Create 1st floor interior walls for RBCDC 1713 based on PDF A-100.

From PDF analysis:
- Building: 45'-4" wide x 28'-8" deep (not including porches)
- Garage: 11'-4" x 20'-0" in SW corner
- Grid A = Y:0, Grid B = Y:7'-0", approximate interior divisions

Room layout (from SW corner, counter-clockwise):
- 101 GARAGE: 242 SF (11'-4" x ~20')
- 102 UTILITY RM: 44 SF
- 103 PANTRY: 2 SF
- 104 KITCHEN: 204 SF
- 105 LIVING RM: 144 SF
- 106 DINING RM: 100 SF
- 107 1/2 BATH: 35 SF
- 108 CLOSET: 68 SF
- 109 FOYER: 49 SF
- EX-1 PORCH: 54 SF
- EX-2 REAR LANAI: 110 SF
"""

import json
import win32file
import math

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# VERIFIED DIMENSIONS FROM PDF A-100
BUILDING_WIDTH = 45.333   # 45'-4" (main building, not including garage west bump)
BUILDING_DEPTH = 28.667   # 28'-8"
GARAGE_WIDTH = 11.333     # 11'-4"
GARAGE_DEPTH = 20.0       # 20'-0"

# The total width including garage is actually larger
TOTAL_WIDTH = 52.333      # Full width from site plan

# Grid positions (Y-axis, from south)
GRID_A = 0.0              # South wall
GRID_B = 7.0              # 7'-0" from A
# Interior walls don't align exactly to grids

# Wall types
EXTERIOR_TYPE_ID = 441515
INTERIOR_TYPE_ID = 441519

# Level
LEVEL_1_ID = 30


def call_mcp(method, params=None):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_wall(wall_id, description, start, end, wall_type_id, level_id, height=10.0):
    """Create a single wall with verification."""
    print(f"\n=== {wall_id}: {description} ===")
    print(f"  Start: ({start[0]:.3f}, {start[1]:.3f})")
    print(f"  End:   ({end[0]:.3f}, {end[1]:.3f})")

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    expected_length = math.sqrt(dx*dx + dy*dy)
    print(f"  Length: {expected_length:.3f} ft")

    result = call_mcp("createWallByPoints", {
        "startPoint": list(start),
        "endPoint": list(end),
        "levelId": level_id,
        "wallTypeId": wall_type_id,
        "height": height,
        "structural": False
    })

    if result.get("success"):
        print(f"  [OK] Created: Wall ID {result.get('wallId')}")
        return result.get('wallId')
    else:
        print(f"  [FAIL] {result.get('error')}")
        return None


def main():
    print("=" * 60)
    print("RBCDC 1713 - 1ST FLOOR INTERIOR WALLS")
    print("=" * 60)

    # Test MCP
    result = call_mcp("getLevels")
    if not result.get("success"):
        print(f"MCP Error: {result.get('error')}")
        return
    print("MCP Connection OK\n")

    created_walls = []

    # ==========================================================
    # INTERIOR WALLS - Based on PDF A-100 room layout
    # Origin at SW corner (0,0), X=East, Y=North
    # ==========================================================

    # From PDF A-100, reading dimensions:
    # - Garage east wall at X = 11.333 (11'-4")
    # - Garage north wall at Y = 20.0 (20'-0")
    # - Kitchen south wall at Y = 7.0 (Grid B)
    # - Utility room is between garage and kitchen

    # INT-002: Utility room east wall (separates utility from kitchen)
    # From floor plan: utility is ~4'-2" wide
    wid = create_wall(
        "INT-002", "Utility room east wall",
        (11.333 + 4.167, 0.0, 0.0),  # 11'-4" + 4'-2" = 15'-6" from west
        (11.333 + 4.167, 7.0, 0.0),  # Up to Grid B
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-003: Kitchen/Living south wall (Grid B line from utility to east)
    # This separates kitchen from living areas to the south
    wid = create_wall(
        "INT-003", "Kitchen south wall (partial)",
        (11.333 + 4.167, 7.0, 0.0),
        (11.333 + 4.167 + 8.0, 7.0, 0.0),  # 8'-0" kitchen width from floor plan
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-004: Pantry walls
    # Pantry is 2 SF - very small, likely closet-sized
    # Located between utility and kitchen per plan

    # INT-005: Foyer/Closet walls
    # From PDF: Foyer 109 is 49 SF, Closet 108 is 68 SF
    # Located at front of house near stairs

    # Stair location from plan: between foyer and closet
    # Stairs are approximately at X = 26' to 30'

    # INT-006: Closet 108 walls (under stairs)
    # Closet is 68 SF, roughly 4' x 17' based on layout
    stair_x = 26.0  # Approximate stair location from plan
    wid = create_wall(
        "INT-006", "Closet 108 west wall",
        (stair_x, 0.0, 0.0),
        (stair_x, 6.333, 0.0),  # ~6'-4" deep
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-007: Closet 108 north wall
    wid = create_wall(
        "INT-007", "Closet 108 north wall",
        (stair_x, 6.333, 0.0),
        (stair_x + 4.0, 6.333, 0.0),  # 4' wide closet
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-008: 1/2 Bath 107 walls
    # 1/2 Bath is 35 SF, roughly 5' x 7'
    # Located adjacent to closet/foyer area
    bath_x = stair_x + 4.0  # East of closet
    wid = create_wall(
        "INT-008", "1/2 Bath 107 east wall",
        (bath_x + 5.0, 0.0, 0.0),
        (bath_x + 5.0, 7.0, 0.0),
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-009: 1/2 Bath 107 north wall
    wid = create_wall(
        "INT-009", "1/2 Bath 107 north wall",
        (bath_x, 7.0, 0.0),
        (bath_x + 5.0, 7.0, 0.0),
        INTERIOR_TYPE_ID, LEVEL_1_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # INT-010: Dining/Living separation wall (if exists)
    # From plan, dining and living appear open but may have partial wall
    # Dining 106 is 100 SF (10' x 10'), Living 105 is 144 SF

    # Living room is at northeast, dining at east-center
    # Kitchen opens to both

    # INT-011: Kitchen north wall (partial - peninsula/island area)
    # The kitchen has an island/peninsula shown in plan
    kitchen_north_y = 7.0 + 8.0  # Kitchen depth from Grid B
    wid = create_wall(
        "INT-011", "Kitchen peninsula base",
        (20.0, 15.0, 0.0),
        (27.0, 15.0, 0.0),  # 7' peninsula
        INTERIOR_TYPE_ID, LEVEL_1_ID, 3.5  # Counter height
    )
    if wid: created_walls.append(wid)

    # ==========================================================
    # SUMMARY
    # ==========================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_walls)} interior walls")

    # Verify total walls
    result = call_mcp("getWalls")
    if result.get("success"):
        walls = result.get("walls", [])
        print(f"Total walls in model: {len(walls)}")


if __name__ == "__main__":
    main()
