#!/usr/bin/env python3
"""
Create walls in Revit from Florida 1713 floor plan - FIXED ORIENTATION
Based on A-100 floor plan from PDF page 5

CRITICAL: The floor plan orientation is:
- SOUTH = Front of house (street facing, PORCH)
- NORTH = Back of house (REAR LANAI)
- EAST = Right side (GARAGE extends here)
- WEST = Left side

From the PDF dimensions (A-100):
Grid spacing (vertical, left to right = west to east):
- Grid 1 to 2: 11'-4"
- Grid 2 to 3: 10'-8"
- Grid 3 to 4: 23'-4" (this includes the garage area)
- Grid 4 to 5: 7'-0"
Total width: ~52'-4" but main house is ~34'

Grid spacing (horizontal, bottom to top = south to north):
- A to B: 6'-0"
- B to C: 9'-0"
- C to D: 10'-0" (approx)
Total depth: ~25' main house + 7' garage extension

Using coordinate system:
- Origin (0,0) at southwest corner of MAIN HOUSE (not garage)
- X increases going EAST (right)
- Y increases going NORTH (up/back)
- Garage extends SOUTH (negative Y) from the main house

Room Layout from A-100:
1st Floor:
- GARAGE (101): Southeast, extends south
- UTILITY RM (102): Next to garage
- PANTRY (103): Small closet
- KITCHEN (104): Center-north area
- LIVING RM (105): Northwest
- DINING RM (106): Center
- 1/2 BATH (107): Near foyer
- CLOSET (108): Under stairs
- FOYER (109): Entry from porch
- REAR LANAI (EX-2): North exterior
- PORCH (EX-1): South entry
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

# Dimensions from A-100 (in feet) - PRECISE from PDF
# Reading the grid dimensions from the PDF:
#   Horizontal (west to east): 1→2=11'-4", 2→3=10'-8", 3→4=23'-4", 4→5=7'-0" = 52'-4" total
#   BUT the main living area is grids 1-4 = 45'-4"
#   Vertical (south to north): see plan

# Looking at the floor plan layout from A-100:
# The house faces SOUTH (PORCH at front/south)
# GARAGE is at the SOUTHEAST corner, extending forward
# Main rooms from left to right (west to east):
#   - LIVING/KITCHEN/DINING on west side
#   - FOYER/STAIRS in center
#   - GARAGE on east side

# Coordinate system: Origin at SW corner of PORCH
# X = West to East (increases right)
# Y = South to North (increases up)

# From PDF measurements:
# Main house width: 34'-0" (grids 1-4 minus garage offset)
# Main house depth: 21'-8" (living area)
# Garage: 11'-4" wide x 17'-8" deep (including the portion next to house)
# Porch depth: 4'-0"

# WALLS based on PDF A-100 dimensions
WALLS = [
    # === EXTERIOR WALLS ===

    # PORCH area (4' deep at front, under main house overhang)
    # Porch spans from foyer to east side

    # West exterior wall (full height)
    {"start": (0, 4), "end": (0, 25.67), "type": "exterior", "name": "West exterior"},

    # South exterior - porch/entry area (4' setback from main)
    {"start": (0, 4), "end": (22, 4), "type": "exterior", "name": "South exterior - main"},

    # GARAGE front wall (extends 7' south of main house line)
    {"start": (22, -3), "end": (34, -3), "type": "exterior", "name": "Garage front (south)"},

    # Garage east wall
    {"start": (34, -3), "end": (34, 21), "type": "exterior", "name": "Garage east wall"},

    # Garage/house step wall
    {"start": (22, 4), "end": (22, -3), "type": "exterior", "name": "Garage west step"},

    # North exterior wall (rear of house)
    {"start": (0, 25.67), "end": (34, 25.67), "type": "exterior", "name": "North exterior"},

    # East exterior above garage (utility/pantry area)
    {"start": (34, 21), "end": (34, 25.67), "type": "exterior", "name": "East exterior - upper"},

    # === INTERIOR WALLS ===

    # Wall between main house and garage/utility area
    {"start": (22, 4), "end": (22, 14), "type": "interior", "name": "House/garage divider"},

    # Utility room / garage separation
    {"start": (22, 14), "end": (34, 14), "type": "interior", "name": "Utility room south"},

    # Closet under stairs
    {"start": (17, 4), "end": (17, 10), "type": "interior", "name": "Stair closet west"},
    {"start": (17, 10), "end": (22, 10), "type": "interior", "name": "Stair closet north"},

    # 1/2 Bath
    {"start": (17, 4), "end": (17, 8), "type": "interior", "name": "1/2 Bath west"},
    {"start": (13, 4), "end": (13, 8), "type": "interior", "name": "1/2 Bath east"},
    {"start": (13, 8), "end": (17, 8), "type": "interior", "name": "1/2 Bath north"},

    # Kitchen/Dining/Living separations
    {"start": (0, 14), "end": (13, 14), "type": "interior", "name": "Living/Kitchen divider"},
    {"start": (13, 8), "end": (13, 14), "type": "interior", "name": "Dining west wall"},

    # Pantry walls
    {"start": (28, 14), "end": (28, 18), "type": "interior", "name": "Pantry west"},
    {"start": (28, 18), "end": (34, 18), "type": "interior", "name": "Pantry north"},

    # Rear lanai partial wall
    {"start": (0, 21), "end": (8, 21), "type": "interior", "name": "Rear lanai separation"},
]

def get_all_walls():
    """Get all existing wall IDs"""
    result = call_mcp("getElementsByCategory", {"category": "Walls"})
    if result.get("success"):
        return [elem["id"] for elem in result.get("elements", [])]
    return []

def delete_walls(wall_ids):
    """Delete walls by IDs"""
    if not wall_ids:
        return {"success": True, "deletedCount": 0}
    return call_mcp("deleteElements", {"elementIds": wall_ids})

def create_walls():
    walls_created = []
    errors = []

    print(f"Creating {len(WALLS)} walls from A-100 floor plan (FIXED ORIENTATION)...")

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
                "type": wall["type"]
            })
            print(f"  Wall {i+1}: Created '{wall['name']}' (ID: {result.get('wallId')})")
        else:
            errors.append({
                "index": i,
                "name": wall["name"],
                "error": result.get("error")
            })
            print(f"  Wall {i+1}: ERROR '{wall['name']}' - {result.get('error')}")

    return {
        "success": len(errors) == 0,
        "walls_created": len(walls_created),
        "errors": len(errors),
        "details": walls_created,
        "error_details": errors
    }

if __name__ == "__main__":
    # First, get and delete all existing walls
    print("Step 1: Getting existing walls...")
    existing_walls = get_all_walls()
    print(f"  Found {len(existing_walls)} existing walls")

    if existing_walls:
        print("Step 2: Deleting existing walls...")
        delete_result = delete_walls(existing_walls)
        if delete_result.get("success"):
            print(f"  Deleted {delete_result.get('deletedCount', 0)} walls")
        else:
            print(f"  Error deleting walls: {delete_result.get('error')}")

    print("\nStep 3: Creating new walls with correct orientation...")
    result = create_walls()
    print("\n" + "="*50)
    print(f"Result: {result['walls_created']} walls created, {result['errors']} errors")
