#!/usr/bin/env python3
"""
Create walls in Revit from Florida 1713 floor plan - CORRECT LAYOUT
Based on A-100 floor plan from PDF page 5

READING THE PLAN CORRECTLY:
- PORCH (EX-1) is at FRONT/SOUTH (bottom of drawing) - street facing
- REAR LANAI (EX-2) is at BACK/NORTH (top of drawing)
- GARAGE (101) is on EAST side (right on drawing), extends forward/south
- LIVING/KITCHEN/DINING are on WEST side (left on drawing)

From PDF A-100 dimensions:
- Grid 1 to 2: 11'-4" (west to east)
- Grid 2 to 3: 10'-8"
- Grid 3 to 4: 23'-4" (includes garage)
- Main house width: 34'-0"

Coordinate system:
- Origin (0,0) at southwest corner of MAIN HOUSE exterior
- X increases going EAST (right)
- Y increases going NORTH (up/back toward rear lanai)
- Porch is at Y=0 to Y=-4 (south of main house, recessed)
- Garage extends from main house line forward (south) by about 7'
"""
import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

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

# Wall type IDs from Revit
EXTERIOR_WALL_TYPE = 441515  # Exterior - Wood Siding on Wood Stud
INTERIOR_WALL_TYPE = 441519  # Interior - 4 1/2" Partition
LEVEL_ID = 30  # L1
HEIGHT = 10.0  # 10 feet (first floor ceiling height)

# ============================================================
# DIMENSIONS FROM A-100 (all in feet)
# ============================================================
# Main house: 34' wide x ~22' deep (main living area)
# Garage: ~12' wide x ~17.67' deep, offset 7' south from main house

# Grid positions (X axis, west to east):
GRID_1 = 0.0       # West edge
GRID_2 = 11.33     # 11'-4" from west
GRID_3 = 22.0      # 10'-8" more (11.33 + 10.67)
GRID_4 = 34.0      # Main house east edge (where garage internal wall is)

# Grid positions (Y axis, south to north):
GRID_A = 0.0       # Main house south exterior wall
GRID_B = 6.0       # 6' north of A
GRID_C = 15.0      # 9' north of B (6+9=15)
GRID_D = 21.67     # Main house north wall (about 21'-8" total depth)

# Offsets for porch and garage:
GARAGE_SOUTH = -7.0      # Garage front wall extends 7' south of main house
GARAGE_WEST = 22.0       # Garage starts at grid 3 (22' from west edge)
GARAGE_EAST = 34.0       # Garage ends at 34'

# Rear lanai:
LANAI_NORTH = 25.67      # Rear lanai extends about 4' north (21.67 + 4)

# ============================================================
# WALL DEFINITIONS - READING FROM THE PLAN
# ============================================================
WALLS = [
    # ====== EXTERIOR WALLS ======

    # WEST EXTERIOR WALL (full height of main house)
    {"start": (0, 0), "end": (0, LANAI_NORTH), "type": "exterior", "name": "West exterior - full"},

    # SOUTH EXTERIOR WALL - Main house portion (west of garage)
    {"start": (0, 0), "end": (GARAGE_WEST, 0), "type": "exterior", "name": "South exterior - main house"},

    # GARAGE STEP - west wall of garage projection
    {"start": (GARAGE_WEST, 0), "end": (GARAGE_WEST, GARAGE_SOUTH), "type": "exterior", "name": "Garage west step wall"},

    # GARAGE SOUTH WALL (front of garage)
    {"start": (GARAGE_WEST, GARAGE_SOUTH), "end": (GARAGE_EAST, GARAGE_SOUTH), "type": "exterior", "name": "Garage front wall (south)"},

    # GARAGE EAST WALL (side of garage)
    {"start": (GARAGE_EAST, GARAGE_SOUTH), "end": (GARAGE_EAST, LANAI_NORTH), "type": "exterior", "name": "Garage/East exterior - full"},

    # NORTH EXTERIOR WALL (rear of house / rear lanai boundary)
    {"start": (0, LANAI_NORTH), "end": (GARAGE_EAST, LANAI_NORTH), "type": "exterior", "name": "North exterior - rear"},

    # ====== INTERIOR WALLS ======

    # GARAGE/UTILITY divider (separates garage from utility room)
    {"start": (GARAGE_WEST, GARAGE_SOUTH), "end": (GARAGE_WEST, 10), "type": "interior", "name": "Garage/Utility divider"},

    # UTILITY ROOM south wall
    {"start": (GARAGE_WEST, 10), "end": (GARAGE_EAST, 10), "type": "interior", "name": "Utility room south wall"},

    # PANTRY walls (small closet between utility and kitchen)
    {"start": (28, 10), "end": (28, 14), "type": "interior", "name": "Pantry west wall"},
    {"start": (28, 14), "end": (GARAGE_EAST, 14), "type": "interior", "name": "Pantry north wall"},

    # FOYER/STAIR area walls
    # 1/2 Bath west wall
    {"start": (15, 0), "end": (15, 6), "type": "interior", "name": "1/2 Bath west wall"},
    # 1/2 Bath north wall
    {"start": (15, 6), "end": (19, 6), "type": "interior", "name": "1/2 Bath north wall"},
    # Closet west wall (under stairs)
    {"start": (19, 0), "end": (19, 10), "type": "interior", "name": "Stair closet west wall"},
    # Closet north wall
    {"start": (19, 10), "end": (GARAGE_WEST, 10), "type": "interior", "name": "Stair closet north wall"},

    # LIVING/DINING/KITCHEN separation
    # Kitchen south wall (partial, separating from dining)
    {"start": (0, 15), "end": (GRID_2, 15), "type": "interior", "name": "Kitchen south wall"},

    # Dining room east wall (partial)
    {"start": (GRID_2, 6), "end": (GRID_2, 15), "type": "interior", "name": "Dining east wall"},

    # REAR LANAI partial wall (separates lanai from interior)
    {"start": (0, GRID_D), "end": (10, GRID_D), "type": "interior", "name": "Rear lanai separation"},
]

def create_walls():
    walls_created = []
    errors = []

    print(f"Creating {len(WALLS)} walls from A-100 floor plan (CORRECT ORIENTATION)...")
    print("Coordinate system: Origin at SW corner, X=East, Y=North")
    print(f"Main house: 34' x 21.67', Garage projects 7' south")
    print()

    for i, wall in enumerate(WALLS):
        start_x, start_y = wall["start"]
        end_x, end_y = wall["end"]

        wall_type_id = EXTERIOR_WALL_TYPE if wall["type"] == "exterior" else INTERIOR_WALL_TYPE

        params = {
            "startPoint": [start_x, start_y, 0.0],
            "endPoint": [end_x, end_y, 0.0],
            "levelId": LEVEL_ID,
            "height": HEIGHT,
            "wallTypeId": wall_type_id
        }

        result = call_mcp("createWallByPoints", params)

        if result.get("success"):
            walls_created.append({
                "index": i,
                "wallId": result.get("wallId"),
                "name": wall["name"],
                "type": wall["type"],
                "start": wall["start"],
                "end": wall["end"]
            })
            print(f"  [{i+1:2d}] OK: '{wall['name']}' ({wall['start']} -> {wall['end']}) ID: {result.get('wallId')}")
        else:
            errors.append({
                "index": i,
                "name": wall["name"],
                "error": result.get("error")
            })
            print(f"  [{i+1:2d}] ERROR: '{wall['name']}' - {result.get('error')}")

    return {
        "success": len(errors) == 0,
        "walls_created": len(walls_created),
        "errors": len(errors),
        "details": walls_created,
        "error_details": errors
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Creating Florida 1713 Floor Plan - CORRECT ORIENTATION")
    print("=" * 60)
    print()

    result = create_walls()

    print()
    print("=" * 60)
    print(f"RESULT: {result['walls_created']} walls created, {result['errors']} errors")
    print("=" * 60)

    if result['errors'] > 0:
        print("\nERRORS:")
        for err in result['error_details']:
            print(f"  - {err['name']}: {err['error']}")
