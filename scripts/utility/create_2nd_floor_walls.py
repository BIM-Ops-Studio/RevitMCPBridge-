#!/usr/bin/env python3
"""
Create 2nd floor walls for RBCDC 1713 2-Story Prototype.

From PDF A-100 (2nd Floor Plan) and elevations:
- 2nd floor elevation: 10'-6" (10.5 ft)
- 2nd floor footprint: Same as main building (no garage below)
- Building width: 52'-4" (52.333 ft) but 2nd floor starts at garage wall
- 2nd floor starts at X = 11.333' (above garage east wall line)
- Building depth: 28'-8" (28.667 ft)

2nd Floor Rooms:
- 200 BEDROOM: 97 SF
- 201 CLOSET: 12 SF
- 202 BEDROOM: 99 SF
- 203 LAV/SHOWER: 39 SF
- 204 BATH: 32 SF
- 205 M/BEDROOM: 164 SF (Master)
- 206 BATH: 39 SF
- 207 STUDY: 28 SF
- 208 HALLWAY: 62 SF
- 209 CLOSET: 12 SF
- 210 CLOSET: 4 SF
- 211 CLOSET: 28 SF
- EX-3 BALCONY: 109 SF
"""

import json
import win32file
import math

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# VERIFIED DIMENSIONS FROM PDF
BUILDING_WIDTH = 52.333   # 52'-4"
BUILDING_DEPTH = 28.667   # 28'-8"
GARAGE_WIDTH = 11.333     # 11'-4"

# 2nd floor starts above garage line
FLOOR2_START_X = GARAGE_WIDTH  # 11.333'
FLOOR2_WIDTH = BUILDING_WIDTH - GARAGE_WIDTH  # 41.0'

# Wall types
EXTERIOR_TYPE_ID = 441515
INTERIOR_TYPE_ID = 441519

# Level
LEVEL_2_ID = 9946  # Actual level ID from Revit model


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
    print("RBCDC 1713 - 2ND FLOOR WALLS")
    print("=" * 60)
    print(f"\n2nd Floor Dimensions:")
    print(f"  Width: {FLOOR2_WIDTH:.3f}' (41'-0\")")
    print(f"  Depth: {BUILDING_DEPTH:.3f}' (28'-8\")")
    print(f"  Start X: {FLOOR2_START_X:.3f}' (above garage)")
    print(f"  Level 2 ID: {LEVEL_2_ID}")

    # Test MCP connection
    result = call_mcp("getLevels")
    if not result.get("success"):
        print(f"\nMCP Error: {result.get('error')}")
        return
    print("\nMCP Connection OK")

    # Show levels for verification
    for level in result.get("levels", []):
        print(f"  Level: {level.get('name')} (ID: {level.get('id')}, Elev: {level.get('elevation'):.2f}')")

    created_walls = []

    # ============================================================
    # 2ND FLOOR EXTERIOR WALLS (Counter-clockwise from SW corner)
    # Note: SW corner of 2nd floor is at (11.333, 0) - above garage wall
    # ============================================================
    print("\n" + "=" * 60)
    print("2ND FLOOR EXTERIOR WALLS")
    print("=" * 60)

    # 2F-EXT-001: South wall (above garage to east edge)
    wid = create_wall(
        "2F-EXT-001", "South wall",
        (FLOOR2_START_X, 0.0, 0.0),
        (BUILDING_WIDTH, 0.0, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-EXT-002: East wall
    wid = create_wall(
        "2F-EXT-002", "East wall",
        (BUILDING_WIDTH, 0.0, 0.0),
        (BUILDING_WIDTH, BUILDING_DEPTH, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-EXT-003: North wall
    wid = create_wall(
        "2F-EXT-003", "North wall",
        (BUILDING_WIDTH, BUILDING_DEPTH, 0.0),
        (FLOOR2_START_X, BUILDING_DEPTH, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-EXT-004: West wall (above garage east wall line)
    wid = create_wall(
        "2F-EXT-004", "West wall",
        (FLOOR2_START_X, BUILDING_DEPTH, 0.0),
        (FLOOR2_START_X, 0.0, 0.0),
        EXTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # ============================================================
    # 2ND FLOOR INTERIOR WALLS
    # Based on room layout from PDF A-100
    # ============================================================
    print("\n" + "=" * 60)
    print("2ND FLOOR INTERIOR WALLS")
    print("=" * 60)

    # From PDF, approximate room divisions:
    # The 2nd floor has a central hallway (208) running east-west
    # Bedrooms on north and south sides
    # Master bedroom (205) at east end with bath (206)

    # Hallway is roughly at Y = 14' (center of building depth)
    HALLWAY_Y_SOUTH = 12.0  # South edge of hallway
    HALLWAY_Y_NORTH = 16.0  # North edge of hallway (4' wide hallway)

    # Room divisions along X axis (from west to east)
    # Bedroom 200 and 202 are on south, 207 Study and 205 Master on north

    # 2F-INT-001: Hallway south wall (partial - from stairs to bedroom partition)
    # Stairs are at west end, hallway extends east
    stairs_x = FLOOR2_START_X + 4.0  # Stair opening ~4' wide

    wid = create_wall(
        "2F-INT-001", "Hallway south wall - west portion",
        (stairs_x, HALLWAY_Y_SOUTH, 0.0),
        (FLOOR2_START_X + 16.0, HALLWAY_Y_SOUTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-002: Hallway north wall - west portion
    wid = create_wall(
        "2F-INT-002", "Hallway north wall - west portion",
        (stairs_x, HALLWAY_Y_NORTH, 0.0),
        (FLOOR2_START_X + 16.0, HALLWAY_Y_NORTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-003: Bedroom 200/202 separation wall
    # These are two bedrooms on the south side
    bedroom_div_x = FLOOR2_START_X + 10.0  # Approximate division

    wid = create_wall(
        "2F-INT-003", "Bedroom 200/202 separation",
        (bedroom_div_x, 0.0, 0.0),
        (bedroom_div_x, HALLWAY_Y_SOUTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-004: Closet 201 wall (in bedroom 200)
    closet_x = FLOOR2_START_X + 2.0

    wid = create_wall(
        "2F-INT-004", "Closet 201 wall",
        (closet_x, 0.0, 0.0),
        (closet_x, 4.0, 0.0),  # Small closet
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-005: Bathroom 203/204 walls
    # These are between bedrooms on south side
    bath_start_x = bedroom_div_x + 5.0

    wid = create_wall(
        "2F-INT-005", "Bath 203/204 west wall",
        (bath_start_x, 0.0, 0.0),
        (bath_start_x, HALLWAY_Y_SOUTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-006: Bath 203/204 separation wall
    bath_div_y = 6.0  # Divide lav/shower from bath

    wid = create_wall(
        "2F-INT-006", "Bath 203/204 separation",
        (bath_start_x, bath_div_y, 0.0),
        (bath_start_x + 7.0, bath_div_y, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-007: Master bedroom/bath wall
    # Master bath (206) is accessed from master bedroom (205)
    master_bath_x = BUILDING_WIDTH - 8.0  # Bath at east end

    wid = create_wall(
        "2F-INT-007", "Master bath 206 west wall",
        (master_bath_x, HALLWAY_Y_NORTH, 0.0),
        (master_bath_x, BUILDING_DEPTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-008: Study 207 wall
    # Study is between hallway and master area on north side
    study_x = FLOOR2_START_X + 12.0

    wid = create_wall(
        "2F-INT-008", "Study 207 east wall",
        (study_x, HALLWAY_Y_NORTH, 0.0),
        (study_x, BUILDING_DEPTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-009: Master bedroom south wall (partial - opens to hallway)
    master_start_x = study_x + 8.0

    wid = create_wall(
        "2F-INT-009", "Master area south wall",
        (master_start_x, HALLWAY_Y_NORTH, 0.0),
        (master_bath_x, HALLWAY_Y_NORTH, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # 2F-INT-010: Closet 211 wall (master closet)
    closet211_x = master_bath_x - 4.0

    wid = create_wall(
        "2F-INT-010", "Closet 211 wall",
        (closet211_x, HALLWAY_Y_NORTH, 0.0),
        (closet211_x, HALLWAY_Y_NORTH + 4.0, 0.0),
        INTERIOR_TYPE_ID, LEVEL_2_ID, 10.0
    )
    if wid: created_walls.append(wid)

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_walls)} walls on 2nd floor")

    # Get total wall count
    result = call_mcp("getWalls")
    if result.get("success"):
        walls = result.get("walls", [])
        print(f"Total walls in model: {len(walls)}")

        # Count by level
        l1_walls = sum(1 for w in walls if w.get("levelId") == 30)
        l2_walls = sum(1 for w in walls if w.get("levelId") == 311)
        print(f"  Level 1 walls: {l1_walls}")
        print(f"  Level 2 walls: {l2_walls}")


if __name__ == "__main__":
    main()
