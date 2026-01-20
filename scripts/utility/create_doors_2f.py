#!/usr/bin/env python3
"""
Create 2nd floor doors for RBCDC 1713 2-Story Prototype.
"""

import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Door type IDs
DOOR_36x80 = 387958   # Door-Passage-Single-Flush 36" x 80"
DOOR_30x80 = 387954   # Door-Passage-Single-Flush 30" x 80"


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


def get_walls_by_level():
    """Get all walls organized by level."""
    result = call_mcp("getWalls")
    if not result.get("success"):
        return {}, {}

    walls = result.get("walls", [])
    l1_walls = {}
    l2_walls = {}

    for w in walls:
        wall_id = w.get("wallId")
        base_level = w.get("baseLevel", "")
        start = w.get("startPoint", {})
        end = w.get("endPoint", {})
        sx, sy = start.get("x", 0), start.get("y", 0)
        ex, ey = end.get("x", 0), end.get("y", 0)

        # Determine orientation
        dx = abs(ex - sx)
        dy = abs(ey - sy)
        orientation = "horizontal" if dx > dy else "vertical"

        wall_data = {
            "id": wall_id,
            "start": (sx, sy),
            "end": (ex, ey),
            "orientation": orientation
        }

        if base_level == "L1":
            l1_walls[wall_id] = wall_data
        elif base_level == "L2":
            l2_walls[wall_id] = wall_data

    return l1_walls, l2_walls


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
    print("RBCDC 1713 - 2ND FLOOR DOOR PLACEMENT")
    print("=" * 60)

    # Test MCP
    result = call_mcp("getLevels")
    if not result.get("success"):
        print(f"MCP Error: {result.get('error')}")
        return
    print("MCP Connection OK\n")

    # Get walls by level
    l1_walls, l2_walls = get_walls_by_level()
    print(f"L1 walls: {len(l1_walls)}")
    print(f"L2 walls: {len(l2_walls)}")

    print("\n2nd Floor Walls:")
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        print(f"  {wid}: ({sx:.1f},{sy:.1f})->({ex:.1f},{ey:.1f}), {w['orientation']}")

    created_doors = []
    BUILDING_DEPTH = 28.667
    L2_ELEVATION = 12.0  # Level 2 is at 12'-0"

    # ============================================================
    # 2ND FLOOR DOORS
    # ============================================================
    print("\n" + "=" * 60)
    print("2ND FLOOR DOORS")
    print("=" * 60)

    # Find walls for door placement
    # Wall 1240926: (15.3,12.0)->(27.3,12.0) - Hallway south wall
    # Wall 1240927: (15.3,16.0)->(27.3,16.0) - Hallway north wall
    # Wall 1240932: (44.3,16.0)->(44.3,28.7) - Master bath wall
    # Wall 1240933: (23.3,16.0)->(23.3,28.7) - Study wall
    # Wall 1240934: (31.3,16.0)->(44.3,16.0) - Master south wall
    # Wall 1240930: (26.3,0.0)->(26.3,12.0) - Bath wall

    # D7: Bedroom 200 door (hallway south wall)
    hallway_south = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        if w["orientation"] == "horizontal" and 11 < sy < 13:
            hallway_south = wid
            break

    if hallway_south:
        door_id = place_door(
            hallway_south,
            DOOR_30x80,
            [18.0, 12.0, L2_ELEVATION],
            "D7: Bedroom 200 Door"
        )
        if door_id: created_doors.append(door_id)

    # D8: Bedroom 202 door (hallway south wall)
    if hallway_south:
        door_id = place_door(
            hallway_south,
            DOOR_30x80,
            [24.0, 12.0, L2_ELEVATION],
            "D8: Bedroom 202 Door"
        )
        if door_id: created_doors.append(door_id)

    # D9: Bath 203/204 door (vertical wall near X=26)
    bath_wall = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        if w["orientation"] == "vertical" and 25 < sx < 27 and sy < 1:
            bath_wall = wid
            break

    if bath_wall:
        door_id = place_door(
            bath_wall,
            DOOR_30x80,
            [26.333, 8.0, L2_ELEVATION],
            "D9: Bath 203/204 Door"
        )
        if door_id: created_doors.append(door_id)

    # D10: Study 207 door (vertical wall near X=23)
    study_wall = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        if w["orientation"] == "vertical" and 22 < sx < 24:
            study_wall = wid
            break

    if study_wall:
        door_id = place_door(
            study_wall,
            DOOR_30x80,
            [23.333, 22.0, L2_ELEVATION],
            "D10: Study 207 Door"
        )
        if door_id: created_doors.append(door_id)

    # D11: Master bedroom entry (horizontal wall near Y=16, between X=31-44)
    master_entry_wall = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        ex, ey = w["end"]
        if w["orientation"] == "horizontal" and 15 < sy < 17 and sx > 30:
            master_entry_wall = wid
            break

    if master_entry_wall:
        door_id = place_door(
            master_entry_wall,
            DOOR_36x80,
            [36.0, 16.0, L2_ELEVATION],
            "D11: Master Bedroom Entry"
        )
        if door_id: created_doors.append(door_id)

    # D12: Master bath door (vertical wall near X=44)
    master_bath_wall = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        if w["orientation"] == "vertical" and 43 < sx < 45:
            master_bath_wall = wid
            break

    if master_bath_wall:
        door_id = place_door(
            master_bath_wall,
            DOOR_30x80,
            [44.333, 22.0, L2_ELEVATION],
            "D12: Master Bath Door"
        )
        if door_id: created_doors.append(door_id)

    # D13: Closet 201 door (vertical wall near X=13)
    closet201_wall = None
    for wid, w in l2_walls.items():
        sx, sy = w["start"]
        if w["orientation"] == "vertical" and 12 < sx < 14:
            closet201_wall = wid
            break

    if closet201_wall:
        door_id = place_door(
            closet201_wall,
            DOOR_30x80,
            [13.333, 2.0, L2_ELEVATION],
            "D13: Closet 201 Door"
        )
        if door_id: created_doors.append(door_id)

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_doors)} doors on 2nd floor")


if __name__ == "__main__":
    main()
