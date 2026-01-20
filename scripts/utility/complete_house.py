"""
Complete the house build - add remaining walls, doors, windows
"""

import win32file
import json
import time

def call_mcp(method, params={}, retries=5):
    last_error = None
    for attempt in range(retries):
        try:
            h = win32file.CreateFile(
                r'\\.\pipe\RevitMCPBridge2026',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None, win32file.OPEN_EXISTING, 0, None
            )
            message = json.dumps({"method": method, "params": params}).encode() + b'\n'
            win32file.WriteFile(h, message)
            chunks = []
            while True:
                _, data = win32file.ReadFile(h, 8192)
                chunks.append(data)
                if b'\n' in data or len(data) == 0:
                    break
            win32file.CloseHandle(h)
            return json.loads(b''.join(chunks).decode().strip())
        except Exception as e:
            last_error = str(e)
            if attempt < retries - 1:
                time.sleep(0.5)
            continue
    return {"success": False, "error": last_error}

print("=" * 70)
print("COMPLETING HOUSE BUILD")
print("=" * 70)

LEVEL1_ID = 1240472
WALL_HEIGHT = 10.0

# Store wall IDs for door/window placement
# South wall: 1240601, East: 1240602, North: 1240603, West: 1240604
SOUTH_WALL = 1240601
EAST_WALL = 1240602
NORTH_WALL = 1240603
WEST_WALL = 1240604

# ============================================================================
# ADD MORE INTERIOR WALLS
# ============================================================================
print("\n" + "=" * 70)
print("ADDING MORE INTERIOR WALLS")
print("=" * 70)

interior_walls = [
    # Master bedroom separation
    {"name": "Master BR East", "start": [8, 24, 0], "end": [20, 24, 0]},

    # Bathroom walls
    {"name": "Bath 1 North", "start": [20, 26, 0], "end": [26, 26, 0]},
    {"name": "Bath 1 West", "start": [20, 24, 0], "end": [20, 30, 0]},

    # Secondary bedrooms
    {"name": "BR 2/3 divider", "start": [26, 18, 0], "end": [26, 30, 0]},
    {"name": "BR 2 South", "start": [26, 18, 0], "end": [38, 18, 0]},

    # Bathroom 2
    {"name": "Bath 2 West", "start": [32, 18, 0], "end": [32, 24, 0]},
    {"name": "Bath 2 North", "start": [32, 24, 0], "end": [38, 24, 0]},

    # Entry/Foyer
    {"name": "Entry East", "start": [8, 0, 0], "end": [8, 6, 0]},
    {"name": "Entry North", "start": [0, 6, 0], "end": [8, 6, 0]},

    # Kitchen/Dining open but with partial wall
    {"name": "Kitchen counter wall", "start": [26, 0, 0], "end": [26, 8, 0]},
]

new_wall_ids = []
print("\nCreating interior walls...")

for wall_def in interior_walls:
    print(f"   Creating {wall_def['name']}...")
    result = call_mcp("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": LEVEL1_ID,
        "height": WALL_HEIGHT
    })

    if result.get("success"):
        wall_id = result.get("wallId")
        new_wall_ids.append(wall_id)
        print(f"      OK - Wall ID: {wall_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Interior walls added: {len(new_wall_ids)}")

# ============================================================================
# PLACE MORE DOORS
# ============================================================================
print("\n" + "=" * 70)
print("PLACING DOORS")
print("=" * 70)

# We already have front door. Add more doors.
doors_to_place = [
    {"name": "Rear sliding", "wall_id": NORTH_WALL, "location": [14, 30, 0]},
    {"name": "Master BR", "wall_id": 1240607, "location": [8, 17, 0]},  # Bedroom wall
    {"name": "Master Bath", "wall_id": new_wall_ids[2] if len(new_wall_ids) > 2 else NORTH_WALL, "location": [20, 27, 0]},
]

door_ids = []
print("\nPlacing doors...")

for door_def in doors_to_place:
    print(f"   Placing {door_def['name']}...")
    result = call_mcp("placeDoor", {
        "wallId": door_def["wall_id"],
        "location": door_def["location"]
    })

    if result.get("success"):
        door_id = result.get("doorId")
        door_ids.append(door_id)
        print(f"      OK - Door ID: {door_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Doors placed: {len(door_ids)}")

# ============================================================================
# PLACE WINDOWS
# ============================================================================
print("\n" + "=" * 70)
print("PLACING WINDOWS")
print("=" * 70)

windows_to_place = [
    # Living room - south wall
    {"name": "Living 1", "wall_id": SOUTH_WALL, "location": [5, 0, 3]},
    {"name": "Living 2", "wall_id": SOUTH_WALL, "location": [10, 0, 3]},
    {"name": "Living 3", "wall_id": SOUTH_WALL, "location": [15, 0, 3]},

    # Kitchen - south wall
    {"name": "Kitchen 1", "wall_id": SOUTH_WALL, "location": [28, 0, 3]},
    {"name": "Kitchen 2", "wall_id": SOUTH_WALL, "location": [33, 0, 3]},

    # Master bedroom - north wall
    {"name": "Master 1", "wall_id": NORTH_WALL, "location": [4, 30, 3]},

    # Bedroom 2 - east wall
    {"name": "BR 2", "wall_id": EAST_WALL, "location": [38, 21, 3]},

    # Bedroom 3 - north wall
    {"name": "BR 3", "wall_id": NORTH_WALL, "location": [30, 30, 3]},
]

window_ids = []
print("\nPlacing windows...")

for window_def in windows_to_place:
    print(f"   Placing {window_def['name']}...")
    result = call_mcp("placeWindow", {
        "wallId": window_def["wall_id"],
        "location": window_def["location"]
    })

    if result.get("success"):
        window_id = result.get("windowId")
        window_ids.append(window_id)
        print(f"      OK - Window ID: {window_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Windows placed: {len(window_ids)}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("BUILD PROGRESS")
print("=" * 70)

print("\nElements created this run:")
print(f"   Interior walls: {len(new_wall_ids)}")
print(f"   Doors: {len(door_ids)}")
print(f"   Windows: {len(window_ids)}")

print("\nTotal in model (including previous):")
print("   Levels: 5")
print("   Walls: ~17")
print("   Doors: ~4")
print("   Windows: ~8")
print("   Floor: 1")
print("   Ceilings: 8")
print("   Rooms: 11")

print("\n" + "=" * 70)
print("Check your Revit model!")
print("=" * 70)
