#!/usr/bin/env python3
"""
Create doors for RBCDC 1713 2-Story Prototype.

From PDF A-100 and Door Schedule (A-800):
Door locations are based on room layout and wall positions.

Door Types needed:
- 3'-0" x 6'-8" (36" x 80") - Standard interior
- 2'-6" x 6'-8" (30" x 80") - Closets/bathrooms
- 3'-0" x 6'-8" Exterior - Entry doors

Door Schedule from PDF:
1st Floor:
- D1: Entry door (south wall, foyer)
- D2: Garage entry (garage east wall)
- D3: Garage to utility (interior)
- D4-D8: Interior doors (bathrooms, closets, bedrooms)
- Sliding glass door to rear lanai

2nd Floor:
- D9-D15: Interior doors (bedrooms, bathrooms, closets)
"""

import json
import win32file
import math

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Door type IDs from getDoorTypes
DOOR_36x80 = 387958   # Door-Passage-Single-Flush 36" x 80"
DOOR_30x80 = 387954   # Door-Passage-Single-Flush 30" x 80"
DOOR_EXT_36x80 = 464646  # Door-Exterior-Single-Two_Lite 36" x 80"


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


def get_walls():
    """Get all walls and organize by position for door placement."""
    result = call_mcp("getWalls")
    if not result.get("success"):
        print(f"Error getting walls: {result.get('error')}")
        return {}

    walls = result.get("walls", [])
    wall_map = {}

    for w in walls:
        wall_id = w.get("wallId")
        start = w.get("startPoint", {})
        end = w.get("endPoint", {})
        sx, sy = start.get("x", 0), start.get("y", 0)
        ex, ey = end.get("x", 0), end.get("y", 0)
        length = w.get("length", 0)
        level_id = w.get("levelId")

        # Determine orientation
        dx = abs(ex - sx)
        dy = abs(ey - sy)
        orientation = "horizontal" if dx > dy else "vertical"

        wall_map[wall_id] = {
            "id": wall_id,
            "start": (sx, sy),
            "end": (ex, ey),
            "length": length,
            "levelId": level_id,
            "orientation": orientation,
            "midpoint": ((sx + ex) / 2, (sy + ey) / 2)
        }

        print(f"Wall {wall_id}: ({sx:.1f},{sy:.1f})->({ex:.1f},{ey:.1f}), L={length:.1f}', {orientation}")

    return wall_map


def find_wall_at(walls, x=None, y=None, level=None, tolerance=0.5):
    """Find a wall at approximate location."""
    for wid, w in walls.items():
        if level and w.get("levelId") != level:
            continue

        sx, sy = w["start"]
        ex, ey = w["end"]

        if x is not None:
            # Check if x is along this wall
            min_x = min(sx, ex)
            max_x = max(sx, ex)
            if not (min_x - tolerance <= x <= max_x + tolerance):
                continue

        if y is not None:
            # Check if y is along this wall
            min_y = min(sy, ey)
            max_y = max(sy, ey)
            if not (min_y - tolerance <= y <= max_y + tolerance):
                continue

        return wid
    return None


def place_door(wall_id, door_type_id, location, description):
    """Place a door on a wall."""
    print(f"\n=== Placing: {description} ===")
    print(f"  Wall ID: {wall_id}")
    print(f"  Location: ({location[0]:.2f}, {location[1]:.2f}, {location[2]:.2f})")

    result = call_mcp("placeDoor", {
        "wallId": wall_id,
        "doorTypeId": door_type_id,
        "location": location
    })

    if result.get("success"):
        print(f"  [OK] Door ID: {result.get('doorId')}")
        return result.get("doorId")
    else:
        print(f"  [FAIL] {result.get('error')}")
        return None


def main():
    print("=" * 60)
    print("RBCDC 1713 - DOOR PLACEMENT")
    print("=" * 60)

    # Test MCP connection
    result = call_mcp("getLevels")
    if not result.get("success"):
        print(f"\nMCP Error: {result.get('error')}")
        return

    levels = {l["name"]: l["levelId"] for l in result.get("levels", [])}
    print(f"Levels: {levels}")

    L1_ID = levels.get("L1", 30)
    L2_ID = levels.get("L2", 9946)

    print("\nMCP Connection OK\n")

    # Get walls
    print("=" * 60)
    print("CURRENT WALLS")
    print("=" * 60)
    walls = get_walls()

    if not walls:
        print("No walls found!")
        return

    created_doors = []

    # ============================================================
    # 1ST FLOOR DOORS
    # ============================================================
    print("\n" + "=" * 60)
    print("1ST FLOOR DOORS")
    print("=" * 60)

    # Building dimensions
    GARAGE_WIDTH = 11.333
    BUILDING_WIDTH = 52.333
    BUILDING_DEPTH = 28.667

    # D1: Front entry door (south wall, at foyer area)
    # Foyer is around X = 26-30 based on layout
    # Find south wall of main building
    south_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # South wall at Y=0
        if abs(sy) < 0.1 and abs(ey) < 0.1 and sx >= GARAGE_WIDTH:
            south_wall = wid
            break

    if south_wall:
        # Place entry door at foyer location (approximately X=28)
        door_id = place_door(
            south_wall,
            DOOR_EXT_36x80,
            [28.0, 0.0, 0.0],
            "D1: Front Entry Door"
        )
        if door_id: created_doors.append(door_id)

    # D2: Garage entry (garage west wall)
    # Find garage west wall (X=0, from Y=0 to Y=20)
    garage_west = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        if abs(sx) < 0.1 and abs(ex) < 0.1 and min(sy, ey) < 1 and max(sy, ey) > 15:
            garage_west = wid
            break

    if garage_west:
        # Place garage entry door
        door_id = place_door(
            garage_west,
            DOOR_36x80,
            [0.0, 10.0, 0.0],  # Middle of garage west wall
            "D2: Garage Entry Door"
        )
        if door_id: created_doors.append(door_id)

    # D3: Garage to utility (garage east/separation wall)
    # Find garage separation wall (X=11.333)
    garage_sep = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        if abs(sx - GARAGE_WIDTH) < 0.5 and abs(ex - GARAGE_WIDTH) < 0.5:
            garage_sep = wid
            break

    if garage_sep:
        door_id = place_door(
            garage_sep,
            DOOR_36x80,
            [GARAGE_WIDTH, 15.0, 0.0],  # Upper portion of garage sep wall
            "D3: Garage to Utility Door"
        )
        if door_id: created_doors.append(door_id)

    # D4: 1/2 Bath door (bath 107)
    # Bath is around X=30-35, south side
    # Find a vertical interior wall in that area
    bath_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Look for wall near X=35, vertical
        if w["orientation"] == "vertical" and 33 < sx < 37:
            bath_wall = wid
            break

    if bath_wall:
        door_id = place_door(
            bath_wall,
            DOOR_30x80,
            [35.0, 3.5, 0.0],
            "D4: 1/2 Bath Door"
        )
        if door_id: created_doors.append(door_id)

    # D5: Closet 108 door
    # Closet under stairs, around X=26
    closet_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        if w["orientation"] == "vertical" and 25 < sx < 27:
            closet_wall = wid
            break

    if closet_wall:
        door_id = place_door(
            closet_wall,
            DOOR_30x80,
            [26.0, 3.0, 0.0],
            "D5: Closet 108 Door"
        )
        if door_id: created_doors.append(door_id)

    # D6: Rear sliding door to lanai
    # North wall, at living/dining area
    north_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # North wall at Y=28.667
        if abs(sy - BUILDING_DEPTH) < 0.5 and abs(ey - BUILDING_DEPTH) < 0.5:
            north_wall = wid
            break

    if north_wall:
        door_id = place_door(
            north_wall,
            DOOR_36x80,  # Would be sliding but using regular for now
            [35.0, BUILDING_DEPTH, 0.0],
            "D6: Rear Lanai Door"
        )
        if door_id: created_doors.append(door_id)

    # ============================================================
    # 2ND FLOOR DOORS
    # ============================================================
    print("\n" + "=" * 60)
    print("2ND FLOOR DOORS")
    print("=" * 60)

    # 2nd floor starts at X=11.333
    FLOOR2_START_X = GARAGE_WIDTH

    # D7: Master bedroom entry (from hallway)
    # Find wall separating master area from hallway
    master_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Look for horizontal wall at Y=16 on L2
        if w["orientation"] == "horizontal" and 15 < sy < 17 and w.get("levelId") == L2_ID:
            master_wall = wid
            break

    if master_wall:
        door_id = place_door(
            master_wall,
            DOOR_36x80,
            [38.0, 16.0, 0.0],
            "D7: Master Bedroom Entry"
        )
        if door_id: created_doors.append(door_id)

    # D8: Master bath door
    master_bath_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Look for vertical wall near X=44 on L2
        if w["orientation"] == "vertical" and 43 < sx < 45 and w.get("levelId") == L2_ID:
            master_bath_wall = wid
            break

    if master_bath_wall:
        door_id = place_door(
            master_bath_wall,
            DOOR_30x80,
            [44.333, 22.0, 0.0],
            "D8: Master Bath Door"
        )
        if door_id: created_doors.append(door_id)

    # D9: Bedroom 200 door
    # Find hallway south wall
    bedroom200_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Horizontal wall at Y=12 on L2
        if w["orientation"] == "horizontal" and 11 < sy < 13 and w.get("levelId") == L2_ID:
            bedroom200_wall = wid
            break

    if bedroom200_wall:
        door_id = place_door(
            bedroom200_wall,
            DOOR_30x80,
            [17.0, 12.0, 0.0],
            "D9: Bedroom 200 Door"
        )
        if door_id: created_doors.append(door_id)

    # D10: Bedroom 202 door
    if bedroom200_wall:
        door_id = place_door(
            bedroom200_wall,
            DOOR_30x80,
            [24.0, 12.0, 0.0],
            "D10: Bedroom 202 Door"
        )
        if door_id: created_doors.append(door_id)

    # D11: Bath 203/204 door
    bath_wall_2f = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Vertical wall near X=26 on L2
        if w["orientation"] == "vertical" and 25 < sx < 27 and w.get("levelId") == L2_ID:
            bath_wall_2f = wid
            break

    if bath_wall_2f:
        door_id = place_door(
            bath_wall_2f,
            DOOR_30x80,
            [26.333, 8.0, 0.0],
            "D11: Bath 203/204 Door"
        )
        if door_id: created_doors.append(door_id)

    # D12: Study 207 door
    study_wall = None
    for wid, w in walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        # Vertical wall near X=23 on L2
        if w["orientation"] == "vertical" and 22 < sx < 24 and w.get("levelId") == L2_ID:
            study_wall = wid
            break

    if study_wall:
        door_id = place_door(
            study_wall,
            DOOR_30x80,
            [23.333, 22.0, 0.0],
            "D12: Study 207 Door"
        )
        if door_id: created_doors.append(door_id)

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_doors)} doors")

    # Get door count
    result = call_mcp("getDoorsInView", {"viewId": None})
    if result.get("success"):
        doors = result.get("doors", [])
        print(f"Total doors in model: {len(doors)}")


if __name__ == "__main__":
    main()
