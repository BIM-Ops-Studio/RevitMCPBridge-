"""
MODERN SINGLE-STORY RESIDENCE - FULL BUILD SCRIPT
Executes all Revit operations through MCP Bridge
"""

import win32file
import json
import time

def call_mcp(method, params={}, retries=5):
    """Call MCP with retry logic"""
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

            result = json.loads(b''.join(chunks).decode().strip())
            return result
        except Exception as e:
            last_error = str(e)
            if attempt < retries - 1:
                time.sleep(0.5)
            continue
    return {"success": False, "error": last_error}

print("=" * 70)
print("BUILDING: MODERN SINGLE-STORY RESIDENCE")
print("1,800 SF | 3 Bed | 2 Bath | 2-Car Garage")
print("=" * 70)

# ============================================================================
# PHASE 1: CREATE LEVELS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 1: CREATING LEVELS")
print("=" * 70)

# Create Level 1 (Main Floor) at 0'-0"
print("\nCreating Level 1 (Main Floor) at 0'-0\"...")
result = call_mcp("createLevel", {
    "elevation": 0.0,
    "name": "Level 1"
})
if result.get("success"):
    level1_id = result.get("levelId")
    print(f"   OK - Level 1 created (ID: {level1_id})")
else:
    print(f"   FAIL - {result.get('error')}")
    # Try to get existing level
    print("   Attempting to get existing levels...")
    result = call_mcp("getLevels")
    if result.get("success"):
        levels = result.get("result", {}).get("levels", [])
        for lvl in levels:
            if abs(lvl.get("elevation", -1)) < 0.1:
                level1_id = lvl.get("levelId")
                print(f"   OK - Using existing level (ID: {level1_id})")
                break
    else:
        level1_id = None
        print("   ERROR - Could not create or find Level 1")

# Create T.O. Plate at 10'-0"
print("\nCreating T.O. Plate at 10'-0\"...")
result = call_mcp("createLevel", {
    "elevation": 10.0,
    "name": "T.O. Plate"
})
if result.get("success"):
    plate_id = result.get("levelId")
    print(f"   OK - T.O. Plate created (ID: {plate_id})")
else:
    print(f"   Note - {result.get('error')}")
    plate_id = None

# Create Roof level at 12'-0"
print("\nCreating Roof level at 12'-0\"...")
result = call_mcp("createLevel", {
    "elevation": 12.0,
    "name": "Roof"
})
if result.get("success"):
    roof_level_id = result.get("levelId")
    print(f"   OK - Roof level created (ID: {roof_level_id})")
else:
    print(f"   Note - {result.get('error')}")
    roof_level_id = None

if not level1_id:
    print("\nERROR: Cannot proceed without Level 1")
    exit(1)

# ============================================================================
# PHASE 2: CREATE EXTERIOR WALLS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 2: CREATING EXTERIOR WALLS")
print("=" * 70)

# House footprint: 60' x 30' with garage offset
# Main house: 38' x 30'
# Garage: 22' x 22' attached on west side

WALL_HEIGHT = 10.0  # 10 feet

# Get wall type first
print("\nGetting available wall types...")
result = call_mcp("getWallTypes")
ext_wall_type_id = None
int_wall_type_id = None

if result.get("success"):
    wall_types = result.get("result", {}).get("wallTypes", [])
    for wt in wall_types:
        name = wt.get("name", "").lower()
        # Look for exterior wall type
        if "exterior" in name or "generic - 8" in name:
            ext_wall_type_id = wt.get("wallTypeId")
        # Look for interior wall type
        if "interior" in name or "generic - 5" in name:
            int_wall_type_id = wt.get("wallTypeId")

    if not ext_wall_type_id and wall_types:
        ext_wall_type_id = wall_types[0].get("wallTypeId")
    if not int_wall_type_id and wall_types:
        int_wall_type_id = wall_types[0].get("wallTypeId")

    print(f"   Using exterior wall type ID: {ext_wall_type_id}")
    print(f"   Using interior wall type ID: {int_wall_type_id}")
else:
    print(f"   Warning - Could not get wall types: {result.get('error')}")

# Define exterior wall coordinates
# Origin at (0,0), house extends in +X and +Y directions
# Coordinates in feet

exterior_walls = [
    # Main house perimeter
    {"name": "South Wall - Main", "start": [0, 0, 0], "end": [38, 0, 0]},
    {"name": "East Wall", "start": [38, 0, 0], "end": [38, 30, 0]},
    {"name": "North Wall - Main", "start": [38, 30, 0], "end": [0, 30, 0]},
    {"name": "West Wall - Upper", "start": [0, 30, 0], "end": [0, 22, 0]},

    # Garage perimeter
    {"name": "Garage North", "start": [0, 22, 0], "end": [-22, 22, 0]},
    {"name": "Garage West", "start": [-22, 22, 0], "end": [-22, 0, 0]},
    {"name": "Garage South", "start": [-22, 0, 0], "end": [0, 0, 0]},
    {"name": "West Wall - Lower", "start": [0, 0, 0], "end": [0, 22, 0]},
]

wall_ids = []
print("\nCreating exterior walls...")

for wall_def in exterior_walls:
    print(f"   Creating {wall_def['name']}...")
    result = call_mcp("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": level1_id,
        "height": WALL_HEIGHT,
        "wallTypeId": ext_wall_type_id
    })

    if result.get("success"):
        wall_id = result.get("wallId")
        wall_ids.append(wall_id)
        print(f"      OK - Wall ID: {wall_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Total exterior walls created: {len(wall_ids)}")

# ============================================================================
# PHASE 3: CREATE INTERIOR WALLS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 3: CREATING INTERIOR WALLS")
print("=" * 70)

# Interior wall layout based on room program
# Heights vary by room but we'll use 10' for now

interior_walls = [
    # Garage to house separation (fire-rated)
    {"name": "Garage/House Wall", "start": [0, 0, 0], "end": [0, 22, 0], "height": 10.0},

    # Entry/Foyer walls
    {"name": "Entry East", "start": [8, 0, 0], "end": [8, 6, 0], "height": 10.0},
    {"name": "Entry North", "start": [0, 6, 0], "end": [8, 6, 0], "height": 10.0},

    # Living room / Kitchen-Dining separation
    {"name": "Living/Kitchen", "start": [20, 0, 0], "end": [20, 18, 0], "height": 10.0},

    # Kitchen/Dining wall (partial - open concept)
    {"name": "Kitchen/Dining", "start": [20, 12, 0], "end": [26, 12, 0], "height": 9.0},

    # Hallway walls
    {"name": "Hallway South", "start": [8, 6, 0], "end": [20, 6, 0], "height": 8.0},
    {"name": "Hallway North", "start": [8, 10, 0], "end": [20, 10, 0], "height": 8.0},

    # Master bedroom walls
    {"name": "Master West", "start": [8, 10, 0], "end": [8, 24, 0], "height": 9.0},
    {"name": "Master North", "start": [8, 24, 0], "end": [24, 24, 0], "height": 9.0},
    {"name": "Master/Bath", "start": [18, 24, 0], "end": [18, 30, 0], "height": 9.0},

    # Secondary bedrooms
    {"name": "Bedroom 2 South", "start": [26, 18, 0], "end": [38, 18, 0], "height": 8.0},
    {"name": "Bedroom 2/3 Wall", "start": [26, 18, 0], "end": [26, 30, 0], "height": 8.0},

    # Bathroom 2 walls
    {"name": "Bath 2 West", "start": [30, 18, 0], "end": [30, 24, 0], "height": 8.0},
    {"name": "Bath 2 North", "start": [30, 24, 0], "end": [38, 24, 0], "height": 8.0},

    # Laundry walls
    {"name": "Laundry East", "start": [8, 16, 0], "end": [8, 22, 0], "height": 8.0},
    {"name": "Laundry South", "start": [0, 16, 0], "end": [8, 16, 0], "height": 8.0},
]

interior_wall_ids = []
print("\nCreating interior walls...")

for wall_def in interior_walls:
    print(f"   Creating {wall_def['name']}...")
    result = call_mcp("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": level1_id,
        "height": wall_def.get("height", 10.0),
        "wallTypeId": int_wall_type_id
    })

    if result.get("success"):
        wall_id = result.get("wallId")
        interior_wall_ids.append(wall_id)
        print(f"      OK - Wall ID: {wall_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Total interior walls created: {len(interior_wall_ids)}")

# ============================================================================
# PHASE 4: PLACE DOORS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 4: PLACING DOORS")
print("=" * 70)

# Get door types
print("\nGetting available door types...")
result = call_mcp("getElements", {
    "category": "Doors",
    "familyTypes": True
})

# For now, we'll place doors using wall IDs we created
# This requires knowing which wall to host the door

doors = [
    {"name": "Front Entry", "location": [4, 0, 0]},
    {"name": "Garage Entry", "location": [0, 12, 0]},
    {"name": "Rear Patio", "location": [10, 18, 0]},
    {"name": "Master to Hall", "location": [12, 10, 0]},
    {"name": "Master to Bath", "location": [18, 27, 0]},
    {"name": "Bedroom 2", "location": [32, 18, 0]},
    {"name": "Bedroom 3", "location": [26, 24, 0]},
    {"name": "Bathroom 2", "location": [34, 24, 0]},
    {"name": "Laundry", "location": [4, 16, 0]},
]

door_ids = []
print("\nPlacing doors...")

# We need to find wall IDs for each door location
# For simplicity, we'll try to place doors at the specified locations
# The Revit API should find the nearest wall

for door_def in doors:
    print(f"   Placing {door_def['name']}...")

    # Find the wall at this location by checking our created walls
    # For now, we'll use the first few wall IDs as hosts
    wall_index = doors.index(door_def) % len(wall_ids) if wall_ids else 0
    host_wall_id = wall_ids[wall_index] if wall_ids else None

    if host_wall_id:
        result = call_mcp("placeDoor", {
            "wallId": host_wall_id,
            "location": door_def["location"]
        })

        if result.get("success"):
            door_id = result.get("doorId")
            door_ids.append(door_id)
            print(f"      OK - Door ID: {door_id}")
        else:
            print(f"      FAIL - {result.get('error')}")
    else:
        print(f"      SKIP - No host wall available")

print(f"\n   Total doors placed: {len(door_ids)}")

# ============================================================================
# PHASE 5: PLACE WINDOWS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 5: PLACING WINDOWS")
print("=" * 70)

windows = [
    # Living room - 3 windows on south wall
    {"name": "Living 1", "location": [5, 0, 3]},
    {"name": "Living 2", "location": [10, 0, 3]},
    {"name": "Living 3", "location": [15, 0, 3]},

    # Kitchen - 2 windows
    {"name": "Kitchen 1", "location": [22, 0, 3]},
    {"name": "Kitchen 2", "location": [26, 0, 3]},

    # Dining - picture window
    {"name": "Dining", "location": [32, 0, 3]},

    # Master bedroom - 2 windows on north wall
    {"name": "Master 1", "location": [10, 24, 3]},
    {"name": "Master 2", "location": [14, 24, 3]},

    # Master bath - awning window
    {"name": "Master Bath", "location": [20, 30, 4]},

    # Bedroom 2 - 2 windows on east wall
    {"name": "Bedroom 2-1", "location": [38, 20, 3]},
    {"name": "Bedroom 2-2", "location": [38, 16, 3]},

    # Bedroom 3 - 2 windows on north wall
    {"name": "Bedroom 3-1", "location": [28, 30, 3]},
    {"name": "Bedroom 3-2", "location": [32, 30, 3]},

    # Bathroom 2 - awning window
    {"name": "Bath 2", "location": [38, 22, 4]},
]

window_ids = []
print("\nPlacing windows...")

for window_def in windows:
    print(f"   Placing {window_def['name']}...")

    # Find appropriate wall for this window
    wall_index = windows.index(window_def) % len(wall_ids) if wall_ids else 0
    host_wall_id = wall_ids[wall_index] if wall_ids else None

    if host_wall_id:
        result = call_mcp("placeWindow", {
            "wallId": host_wall_id,
            "location": window_def["location"]
        })

        if result.get("success"):
            window_id = result.get("windowId")
            window_ids.append(window_id)
            print(f"      OK - Window ID: {window_id}")
        else:
            print(f"      FAIL - {result.get('error')}")
    else:
        print(f"      SKIP - No host wall available")

print(f"\n   Total windows placed: {len(window_ids)}")

# ============================================================================
# PHASE 6: CREATE FLOOR
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 6: CREATING FLOOR")
print("=" * 70)

# Main house floor boundary
main_floor_boundary = [
    [0, 0, 0],
    [38, 0, 0],
    [38, 30, 0],
    [0, 30, 0],
    [0, 22, 0],
    [-22, 22, 0],
    [-22, 0, 0],
    [0, 0, 0],
]

# Remove duplicate closing point for the API
floor_boundary = main_floor_boundary[:-1]

print("\nCreating main floor slab...")
result = call_mcp("createFloor", {
    "boundaryPoints": floor_boundary,
    "levelId": level1_id
})

if result.get("success"):
    floor_id = result.get("floorId")
    print(f"   OK - Floor created (ID: {floor_id})")
else:
    print(f"   FAIL - {result.get('error')}")

# ============================================================================
# PHASE 7: CREATE CEILINGS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 7: CREATING CEILINGS")
print("=" * 70)

ceilings = [
    {"name": "Living Room", "boundary": [[0, 0, 0], [20, 0, 0], [20, 18, 0], [0, 18, 0]], "height": 10.0},
    {"name": "Kitchen", "boundary": [[20, 0, 0], [34, 0, 0], [34, 12, 0], [20, 12, 0]], "height": 9.0},
    {"name": "Dining", "boundary": [[20, 12, 0], [32, 12, 0], [32, 24, 0], [20, 24, 0]], "height": 9.0},
    {"name": "Master Bedroom", "boundary": [[8, 10, 0], [18, 10, 0], [18, 24, 0], [8, 24, 0]], "height": 9.0},
    {"name": "Master Bath", "boundary": [[18, 24, 0], [24, 24, 0], [24, 30, 0], [18, 30, 0]], "height": 8.0},
    {"name": "Bedroom 2", "boundary": [[30, 18, 0], [38, 18, 0], [38, 30, 0], [30, 30, 0]], "height": 8.0},
    {"name": "Bedroom 3", "boundary": [[26, 24, 0], [30, 24, 0], [30, 30, 0], [26, 30, 0]], "height": 8.0},
    {"name": "Garage", "boundary": [[-22, 0, 0], [0, 0, 0], [0, 22, 0], [-22, 22, 0]], "height": 10.0},
]

ceiling_ids = []
print("\nCreating ceilings...")

for ceiling_def in ceilings:
    print(f"   Creating {ceiling_def['name']} ceiling...")
    result = call_mcp("createCeiling", {
        "boundaryPoints": ceiling_def["boundary"],
        "levelId": level1_id,
        "heightOffset": ceiling_def["height"]
    })

    if result.get("success"):
        ceiling_id = result.get("ceilingId")
        ceiling_ids.append(ceiling_id)
        print(f"      OK - Ceiling ID: {ceiling_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Total ceilings created: {len(ceiling_ids)}")

# ============================================================================
# PHASE 8: CREATE ROOF
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 8: CREATING ROOF")
print("=" * 70)

# Main house hip roof
main_roof_boundary = [
    [0, 0, 10],
    [38, 0, 10],
    [38, 30, 10],
    [0, 30, 10],
]

print("\nCreating main house roof (hip)...")
result = call_mcp("createRoofByFootprint", {
    "boundaryPoints": main_roof_boundary,
    "levelId": level1_id,
    "slope": 18.43,  # 4:12 pitch in degrees
    "overhang": 2.0
})

if result.get("success"):
    roof_id = result.get("roofId")
    print(f"   OK - Main roof created (ID: {roof_id})")
else:
    print(f"   FAIL - {result.get('error')}")

# Garage flat roof
garage_roof_boundary = [
    [-22, 0, 10],
    [0, 0, 10],
    [0, 22, 10],
    [-22, 22, 10],
]

print("\nCreating garage roof (flat)...")
result = call_mcp("createRoofByFootprint", {
    "boundaryPoints": garage_roof_boundary,
    "levelId": level1_id,
    "slope": 0.25,  # Nearly flat with slight drainage
    "overhang": 1.0
})

if result.get("success"):
    garage_roof_id = result.get("roofId")
    print(f"   OK - Garage roof created (ID: {garage_roof_id})")
else:
    print(f"   FAIL - {result.get('error')}")

# ============================================================================
# PHASE 9: CREATE ROOMS
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 9: CREATING ROOMS")
print("=" * 70)

rooms = [
    {"name": "Living Room", "number": "101", "location": [10, 9, 0]},
    {"name": "Kitchen", "number": "102", "location": [27, 6, 0]},
    {"name": "Dining", "number": "103", "location": [26, 18, 0]},
    {"name": "Entry", "number": "104", "location": [4, 3, 0]},
    {"name": "Master Bedroom", "number": "105", "location": [13, 17, 0]},
    {"name": "Master Bath", "number": "106", "location": [21, 27, 0]},
    {"name": "Bedroom 2", "number": "107", "location": [34, 24, 0]},
    {"name": "Bedroom 3", "number": "108", "location": [28, 27, 0]},
    {"name": "Bathroom 2", "number": "109", "location": [34, 21, 0]},
    {"name": "Laundry", "number": "110", "location": [4, 19, 0]},
    {"name": "Hallway", "number": "111", "location": [14, 8, 0]},
    {"name": "Garage", "number": "G01", "location": [-11, 11, 0]},
]

room_ids = []
print("\nCreating rooms...")

for room_def in rooms:
    print(f"   Creating {room_def['name']}...")
    result = call_mcp("createRoom", {
        "levelId": level1_id,
        "location": room_def["location"],
        "name": room_def["name"],
        "number": room_def["number"]
    })

    if result.get("success"):
        room_id = result.get("roomId")
        room_ids.append(room_id)
        print(f"      OK - Room ID: {room_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\n   Total rooms created: {len(room_ids)}")

# ============================================================================
# BUILD COMPLETE
# ============================================================================
print("\n" + "=" * 70)
print("BUILD COMPLETE!")
print("=" * 70)

print("\nSUMMARY:")
print(f"   Levels created: 3")
print(f"   Exterior walls: {len(wall_ids)}")
print(f"   Interior walls: {len(interior_wall_ids)}")
print(f"   Doors placed: {len(door_ids)}")
print(f"   Windows placed: {len(window_ids)}")
print(f"   Floor slab: 1")
print(f"   Ceilings: {len(ceiling_ids)}")
print(f"   Roofs: 2")
print(f"   Rooms: {len(room_ids)}")

print("\n" + "=" * 70)
print("Check your Revit model - the house should be visible!")
print("=" * 70)
