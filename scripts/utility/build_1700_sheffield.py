"""
Build 1700 West Sheffield Road - Single Family Residence
Based on construction documents analysis

Building Specs:
- Living Area: 1,402 SF
- Under Roof: 2,110 SF (with garage/porches)
- Wall Height: 10'-0"
- Roof: Hip, 4:12 pitch
- Exterior: Stucco
"""
import win32file
import json
import time
import sys

def call_mcp(method, params={}, retries=5):
    """Call MCP server via named pipe"""
    last_error = None
    for attempt in range(retries):
        try:
            pipe = win32file.CreateFile(
                r'\\.\pipe\RevitMCPPipe',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )

            request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": f"tools/{method}",
                "params": {"arguments": params}
            })

            win32file.WriteFile(pipe, request.encode())
            result, data = win32file.ReadFile(pipe, 65536)
            win32file.CloseHandle(pipe)

            response = json.loads(data.decode())
            if "result" in response:
                content = response["result"].get("content", [])
                if content:
                    return json.loads(content[0].get("text", "{}"))
            return response

        except Exception as e:
            last_error = e
            time.sleep(0.3)

    return {"success": False, "error": str(last_error)}

def main():
    print("=" * 70)
    print("BUILDING: 1700 WEST SHEFFIELD ROAD")
    print("AVON PARK, FLORIDA - SINGLE FAMILY RESIDENCE")
    print("=" * 70)

    # ==========================================================================
    # DIMENSIONS FROM CONSTRUCTION DOCUMENTS
    # Based on foundation plan, floor plan, and building calcs
    # ==========================================================================

    # Overall building footprint (from foundation plan S1)
    # Main house: approximately 38' x 35'
    # Garage wing: approximately 22' x 20' extending from left side

    # Convert to decimal feet for Revit
    # Using 0,0 as bottom-left corner of main house

    MAIN_WIDTH = 38.0      # Main house width (E-W)
    MAIN_DEPTH = 35.0      # Main house depth (N-S)
    GARAGE_WIDTH = 22.0    # Garage width
    GARAGE_DEPTH = 20.0    # Garage depth
    WALL_HEIGHT = 10.0     # 10'-0" wall height

    # ==========================================================================
    # STEP 1: CREATE LEVELS
    # ==========================================================================
    print("\n[1/8] Creating Levels...")

    levels = [
        ("Level 1", 0.0),
        ("T.O. Plate", 10.0),
        ("Roof", 14.0)  # Hip roof peak ~4' above plate
    ]

    for name, elevation in levels:
        result = call_mcp("createLevel", {
            "name": name,
            "elevation": elevation
        })
        if result.get("success"):
            print(f"  + Level '{name}' at {elevation}'")
        else:
            print(f"  - Level '{name}': {result.get('error', 'exists')}")

    # ==========================================================================
    # STEP 2: CREATE EXTERIOR WALLS - MAIN HOUSE
    # ==========================================================================
    print("\n[2/8] Creating Exterior Walls - Main House...")

    # Main house perimeter (counterclockwise from SW corner)
    # SW corner at (0, 0)
    main_exterior = [
        # South wall (front)
        {"start": (0, 0), "end": (MAIN_WIDTH, 0), "name": "South - Front"},
        # East wall
        {"start": (MAIN_WIDTH, 0), "end": (MAIN_WIDTH, MAIN_DEPTH), "name": "East"},
        # North wall (back)
        {"start": (MAIN_WIDTH, MAIN_DEPTH), "end": (0, MAIN_DEPTH), "name": "North - Back"},
        # West wall (partial - garage connection)
        {"start": (0, MAIN_DEPTH), "end": (0, GARAGE_DEPTH), "name": "West - Upper"},
        # West wall (lower - to garage)
        {"start": (0, GARAGE_DEPTH), "end": (0, 0), "name": "West - Lower"},
    ]

    walls_created = 0
    for wall in main_exterior:
        result = call_mcp("createWall", {
            "startX": wall["start"][0],
            "startY": wall["start"][1],
            "endX": wall["end"][0],
            "endY": wall["end"][1],
            "height": WALL_HEIGHT,
            "levelName": "Level 1"
        })
        if result.get("success"):
            walls_created += 1
            print(f"  + {wall['name']}")

    # ==========================================================================
    # STEP 3: CREATE EXTERIOR WALLS - GARAGE
    # ==========================================================================
    print("\n[3/8] Creating Exterior Walls - 2-Car Garage...")

    # Garage attached to left side of main house
    # Garage SW corner at (-GARAGE_WIDTH, 0)
    garage_exterior = [
        # South wall (garage front)
        {"start": (-GARAGE_WIDTH, 0), "end": (0, 0), "name": "Garage - South"},
        # West wall
        {"start": (-GARAGE_WIDTH, 0), "end": (-GARAGE_WIDTH, GARAGE_DEPTH), "name": "Garage - West"},
        # North wall
        {"start": (-GARAGE_WIDTH, GARAGE_DEPTH), "end": (0, GARAGE_DEPTH), "name": "Garage - North"},
    ]

    for wall in garage_exterior:
        result = call_mcp("createWall", {
            "startX": wall["start"][0],
            "startY": wall["start"][1],
            "endX": wall["end"][0],
            "endY": wall["end"][1],
            "height": WALL_HEIGHT,
            "levelName": "Level 1"
        })
        if result.get("success"):
            walls_created += 1
            print(f"  + {wall['name']}")

    print(f"\n  Total exterior walls: {walls_created}")

    # ==========================================================================
    # STEP 4: CREATE INTERIOR WALLS
    # ==========================================================================
    print("\n[4/8] Creating Interior Walls...")

    # Room divisions based on floor plan analysis
    # Approximate room sizes from 1,402 SF living area

    interior_walls = [
        # Entry/Foyer partition (6' deep)
        {"start": (0, 6), "end": (10, 6), "name": "Entry - North wall"},
        {"start": (10, 0), "end": (10, 6), "name": "Entry - East wall"},

        # Living Room / Family division (at ~18')
        {"start": (10, 0), "end": (10, 18), "name": "Living/Family division"},

        # Kitchen back wall (at 26' from south)
        {"start": (0, 26), "end": (18, 26), "name": "Kitchen - North wall"},

        # Hallway wall (18' from west)
        {"start": (18, 18), "end": (18, MAIN_DEPTH), "name": "Hallway - West"},
        {"start": (18, 26), "end": (MAIN_WIDTH, 26), "name": "Hallway - South extension"},

        # Master Bedroom partition
        {"start": (0, 18), "end": (12, 18), "name": "Master - South wall"},
        {"start": (12, 18), "end": (12, 26), "name": "Master Bath - East wall"},

        # Master closet
        {"start": (0, 22), "end": (6, 22), "name": "Master Closet - South"},
        {"start": (6, 22), "end": (6, 26), "name": "Master Closet - East"},

        # Bedroom 2 (back right corner)
        {"start": (26, 26), "end": (26, MAIN_DEPTH), "name": "Bedroom 2 - West"},
        {"start": (26, MAIN_DEPTH), "end": (MAIN_WIDTH, MAIN_DEPTH), "name": "Bedroom 2 - already exterior"},

        # Bedroom 3 (front right)
        {"start": (26, 18), "end": (MAIN_WIDTH, 18), "name": "Bedroom 3 - North"},
        {"start": (26, 0), "end": (26, 26), "name": "Bedrooms - West wall"},

        # Bath 2 (between bedrooms)
        {"start": (26, 22), "end": (32, 22), "name": "Bath 2 - South"},
        {"start": (32, 22), "end": (32, 26), "name": "Bath 2 - East"},

        # Laundry (in garage area, adjacent to kitchen)
        {"start": (-8, 12), "end": (0, 12), "name": "Laundry - South"},
        {"start": (-8, 12), "end": (-8, GARAGE_DEPTH), "name": "Laundry - West"},
    ]

    interior_count = 0
    for wall in interior_walls:
        result = call_mcp("createWall", {
            "startX": wall["start"][0],
            "startY": wall["start"][1],
            "endX": wall["end"][0],
            "endY": wall["end"][1],
            "height": WALL_HEIGHT,
            "levelName": "Level 1"
        })
        if result.get("success"):
            interior_count += 1
            print(f"  + {wall['name']}")
        else:
            print(f"  - {wall['name']}: {result.get('error', 'failed')}")

    print(f"\n  Interior walls created: {interior_count}")

    # ==========================================================================
    # STEP 5: PLACE DOORS
    # ==========================================================================
    print("\n[5/8] Placing Doors...")

    # Door schedule from construction documents:
    # D1: 3'-0" x 6'-8" Entry
    # D2: 2'-8" x 6'-8" Interior
    # D3: 2'-6" x 6'-8" Interior
    # D4: 6'-0" x 6'-8" Sliding glass
    # Plus garage door and service doors

    doors = [
        # Entry door (front, center of entry area)
        {"x": 5, "y": 0, "name": "Front Entry"},
        # Rear sliding glass door (kitchen/dining to patio)
        {"x": 9, "y": MAIN_DEPTH, "name": "Rear Slider"},
        # Master bedroom
        {"x": 6, "y": 18, "name": "Master Bedroom"},
        # Master bath
        {"x": 9, "y": 22, "name": "Master Bath"},
        # Master closet
        {"x": 3, "y": 22, "name": "Master Closet"},
        # Bedroom 2
        {"x": 20, "y": 30, "name": "Bedroom 2"},
        # Bedroom 3
        {"x": 20, "y": 12, "name": "Bedroom 3"},
        # Bath 2
        {"x": 29, "y": 22, "name": "Bath 2"},
        # Laundry
        {"x": -4, "y": 12, "name": "Laundry"},
        # Garage service door
        {"x": 0, "y": 16, "name": "Garage Service"},
    ]

    doors_placed = 0
    for door in doors:
        result = call_mcp("placeDoor", {
            "x": door["x"],
            "y": door["y"],
            "levelName": "Level 1"
        })
        if result.get("success"):
            doors_placed += 1
            print(f"  + {door['name']}")
        else:
            print(f"  - {door['name']}: {result.get('error', 'failed')}")

    print(f"\n  Doors placed: {doors_placed}")

    # ==========================================================================
    # STEP 6: PLACE WINDOWS
    # ==========================================================================
    print("\n[6/8] Placing Windows...")

    # Window schedule from construction documents:
    # Type A: Larger windows (living, family)
    # Type B: Bedroom windows
    # Type C: Smaller (bath, utility)

    windows = [
        # Living room - front (3 windows)
        {"x": 12, "y": 0, "name": "Living 1"},
        {"x": 16, "y": 0, "name": "Living 2"},
        {"x": 20, "y": 0, "name": "Living 3"},
        # Family/Dining - side
        {"x": MAIN_WIDTH, "y": 22, "name": "Family - East"},
        # Kitchen - back
        {"x": 6, "y": 26, "name": "Kitchen 1"},
        {"x": 12, "y": 26, "name": "Kitchen 2"},
        # Master Bedroom
        {"x": 0, "y": 20, "name": "Master - West"},
        {"x": 6, "y": MAIN_DEPTH, "name": "Master - North"},
        # Bedroom 2
        {"x": 30, "y": MAIN_DEPTH, "name": "Bedroom 2 - North"},
        {"x": MAIN_WIDTH, "y": 30, "name": "Bedroom 2 - East"},
        # Bedroom 3
        {"x": 30, "y": 0, "name": "Bedroom 3 - South"},
        {"x": MAIN_WIDTH, "y": 12, "name": "Bedroom 3 - East"},
        # Bath 2
        {"x": MAIN_WIDTH, "y": 24, "name": "Bath 2"},
        # Laundry
        {"x": -GARAGE_WIDTH, "y": 16, "name": "Laundry"},
    ]

    windows_placed = 0
    for window in windows:
        result = call_mcp("placeWindow", {
            "x": window["x"],
            "y": window["y"],
            "levelName": "Level 1"
        })
        if result.get("success"):
            windows_placed += 1
            print(f"  + {window['name']}")
        else:
            print(f"  - {window['name']}: {result.get('error', 'failed')}")

    print(f"\n  Windows placed: {windows_placed}")

    # ==========================================================================
    # STEP 7: CREATE ROOMS
    # ==========================================================================
    print("\n[7/8] Creating Rooms...")

    # Room names and approximate center points
    rooms = [
        {"name": "Entry", "x": 5, "y": 3},
        {"name": "Living", "x": 18, "y": 9},
        {"name": "Family/Dining", "x": 5, "y": 12},
        {"name": "Kitchen", "x": 9, "y": 22},
        {"name": "Master Bedroom", "x": 6, "y": 30},
        {"name": "Master Bath", "x": 9, "y": 24},
        {"name": "Master Closet", "x": 3, "y": 24},
        {"name": "Hallway", "x": 22, "y": 24},
        {"name": "Bedroom 2", "x": 32, "y": 30},
        {"name": "Bedroom 3", "x": 32, "y": 9},
        {"name": "Bath 2", "x": 29, "y": 24},
        {"name": "Laundry", "x": -4, "y": 16},
        {"name": "2-Car Garage", "x": -11, "y": 10},
    ]

    rooms_created = 0
    for room in rooms:
        result = call_mcp("createRoom", {
            "locationX": room["x"],
            "locationY": room["y"],
            "levelName": "Level 1",
            "roomName": room["name"]
        })
        if result.get("success"):
            rooms_created += 1
            print(f"  + {room['name']}")
        else:
            print(f"  - {room['name']}: {result.get('error', 'failed')}")

    print(f"\n  Rooms created: {rooms_created}")

    # ==========================================================================
    # STEP 8: CREATE FLOOR SLAB
    # ==========================================================================
    print("\n[8/8] Creating Floor Slab...")

    # Main house slab
    result = call_mcp("createFloor", {
        "boundaryPoints": [
            {"x": -GARAGE_WIDTH, "y": 0},
            {"x": -GARAGE_WIDTH, "y": GARAGE_DEPTH},
            {"x": 0, "y": GARAGE_DEPTH},
            {"x": 0, "y": MAIN_DEPTH},
            {"x": MAIN_WIDTH, "y": MAIN_DEPTH},
            {"x": MAIN_WIDTH, "y": 0},
            {"x": -GARAGE_WIDTH, "y": 0}
        ],
        "levelName": "Level 1"
    })

    if result.get("success"):
        print("  + Floor slab created")
    else:
        print(f"  - Floor slab: {result.get('error', 'failed')}")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 70)
    print("BUILD SUMMARY - 1700 WEST SHEFFIELD ROAD")
    print("=" * 70)
    print(f"""
    Levels:           3 (Level 1, T.O. Plate, Roof)
    Exterior Walls:   {walls_created}
    Interior Walls:   {interior_count}
    Doors:            {doors_placed}
    Windows:          {windows_placed}
    Rooms:            {rooms_created}
    Floor Slab:       1

    Building Dimensions:
    - Main House: {MAIN_WIDTH}' x {MAIN_DEPTH}'
    - Garage: {GARAGE_WIDTH}' x {GARAGE_DEPTH}'
    - Wall Height: {WALL_HEIGHT}'

    NOTE: Hip roof not yet created (requires different API approach)
    """)
    print("=" * 70)
    print("Model created! Check your Revit views.")
    print("=" * 70)

if __name__ == "__main__":
    main()
