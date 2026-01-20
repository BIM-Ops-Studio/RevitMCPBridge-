#!/usr/bin/env python3
"""
Create walls for 950 House Remodel based on PDF floor plan dimensions.
Dimensions extracted visually from Sheet A-100 and A-141.

Building: 950 W. 1ST ST., Riviera Beach, FL
Scale: 1/4" = 1'-0"
"""

import json
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, parameters):
    """Send a request to the MCP server and return the response"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )

        request = {"method": method, "parameters": parameters}
        request_json = json.dumps(request)
        win32file.WriteFile(handle, request_json.encode('utf-8'))
        result, data = win32file.ReadFile(handle, 64 * 1024)
        win32file.CloseHandle(handle)

        return json.loads(data.decode('utf-8'))

    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running. Start it in Revit."}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_wall(start_x, start_y, end_x, end_y, level_id=30, height=10.0, wall_type=None):
    """Create a wall from start to end point"""
    params = {
        "startPoint": {"x": start_x, "y": start_y, "z": 0},
        "endPoint": {"x": end_x, "y": end_y, "z": 0},
        "levelId": level_id,
        "height": height
    }
    if wall_type:
        params["wallType"] = wall_type

    result = send_mcp_request("createWall", params)
    return result

def main():
    print("=" * 60)
    print("950 House Remodel - Wall Creation from PDF Dimensions")
    print("=" * 60)

    # First, verify MCP connection by getting levels
    print("\n[1] Checking MCP connection...")
    levels = send_mcp_request("getLevels", {})

    if not levels.get("success"):
        print(f"ERROR: Cannot connect to Revit MCP: {levels.get('error')}")
        print("\nMake sure:")
        print("  1. Revit 2026 is open")
        print("  2. A project is open")
        print("  3. MCP Server is started (click button in Revit)")
        return False

    print("SUCCESS: MCP connection OK")
    level_list = levels.get("levels", [])
    print(f"Found {len(level_list)} levels:")
    for lvl in level_list:
        print(f"  - {lvl.get('name')} (ID: {lvl.get('id')}, Elevation: {lvl.get('elevation')})")

    # Find Level 1 or first level at elevation 0
    level_id = 30  # Default
    for lvl in level_list:
        if lvl.get("elevation", -1) == 0 or "First" in lvl.get("name", "") or "Level 1" in lvl.get("name", ""):
            level_id = lvl.get("id")
            print(f"\nUsing level: {lvl.get('name')} (ID: {level_id})")
            break

    # Get available wall types
    print("\n[2] Getting available wall types...")
    wall_types = send_mcp_request("getWallTypes", {})
    if wall_types.get("success"):
        types = wall_types.get("wallTypes", [])
        print(f"Found {len(types)} wall types")
        # Find a suitable exterior wall type
        exterior_type = None
        generic_type = None
        for wt in types:
            name = wt.get("name", "").lower()
            if "exterior" in name or "8\" cmu" in name.lower():
                exterior_type = wt.get("name")
                break
            if "generic" in name:
                generic_type = wt.get("name")

        wall_type = exterior_type or generic_type
        print(f"Using wall type: {wall_type or 'Default'}")
    else:
        wall_type = None
        print("WARNING: Could not get wall types, using default")

    # =====================================================
    # WALL COORDINATES - Based on PDF Floor Plan A-100
    # =====================================================
    # Origin at bottom-left corner of building (SW corner)
    # Building runs roughly North-South
    # Dimensions from PDF:
    # - Building width: ~32'-0" (E-W)
    # - Building depth: ~47'-6" (N-S)
    # - Garage infill: 10'-6" x 9'-8"
    #
    # Coordinate system: X = East, Y = North
    # =====================================================

    print("\n[3] Creating exterior walls...")

    # Define building dimensions in feet
    # Main building perimeter (approximate from floor plan)
    BUILDING_WIDTH = 32.0   # E-W dimension
    BUILDING_DEPTH = 47.5   # N-S dimension
    WALL_HEIGHT = 10.0      # Standard wall height

    # Garage dimensions (from A-141)
    GARAGE_WIDTH = 10.5     # 10'-6"
    GARAGE_DEPTH = 9.67     # 9'-8"

    # Define exterior walls as (start_x, start_y, end_x, end_y, description)
    exterior_walls = [
        # Main building perimeter - clockwise from SW corner
        # South wall (front)
        (0, 0, BUILDING_WIDTH, 0, "South Exterior - Front"),

        # East wall (right side when facing building)
        (BUILDING_WIDTH, 0, BUILDING_WIDTH, BUILDING_DEPTH, "East Exterior"),

        # North wall (rear)
        (BUILDING_WIDTH, BUILDING_DEPTH, 0, BUILDING_DEPTH, "North Exterior - Rear"),

        # West wall (left side) - with garage notch
        # From NW corner going south to garage
        (0, BUILDING_DEPTH, 0, GARAGE_DEPTH + 10, "West Exterior - North of Garage"),

        # Garage walls (infill area from A-141)
        # Garage is at SW corner based on floor plan
        (0, GARAGE_DEPTH + 10, GARAGE_WIDTH, GARAGE_DEPTH + 10, "Garage - North Wall"),
        (GARAGE_WIDTH, GARAGE_DEPTH + 10, GARAGE_WIDTH, 0, "Garage - East Wall (interior)"),

        # Complete west wall from garage to SW corner
        # (0, GARAGE_DEPTH, 0, 0, "West Exterior - South"),  # Already part of perimeter
    ]

    # Actually, let me simplify - create the main rectangular building first
    # without the garage notch, then we can adjust

    simple_walls = [
        # Main building rectangle
        (0, 0, BUILDING_WIDTH, 0, "South Wall"),
        (BUILDING_WIDTH, 0, BUILDING_WIDTH, BUILDING_DEPTH, "East Wall"),
        (BUILDING_WIDTH, BUILDING_DEPTH, 0, BUILDING_DEPTH, "North Wall"),
        (0, BUILDING_DEPTH, 0, 0, "West Wall"),
    ]

    created_walls = []
    failed_walls = []

    for wall_def in simple_walls:
        start_x, start_y, end_x, end_y, desc = wall_def
        print(f"\n  Creating: {desc}")
        print(f"    From: ({start_x:.2f}, {start_y:.2f}) To: ({end_x:.2f}, {end_y:.2f})")

        result = create_wall(start_x, start_y, end_x, end_y, level_id, WALL_HEIGHT, wall_type)

        if result.get("success"):
            wall_id = result.get("wallId", result.get("elementId", "unknown"))
            print(f"    SUCCESS: Wall ID = {wall_id}")
            created_walls.append({"desc": desc, "id": wall_id})
        else:
            error = result.get("error", "Unknown error")
            print(f"    FAILED: {error}")
            failed_walls.append({"desc": desc, "error": error})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created: {len(created_walls)} walls")
    print(f"Failed:  {len(failed_walls)} walls")

    if created_walls:
        print("\nCreated walls:")
        for w in created_walls:
            print(f"  - {w['desc']} (ID: {w['id']})")

    if failed_walls:
        print("\nFailed walls:")
        for w in failed_walls:
            print(f"  - {w['desc']}: {w['error']}")

    print("\nDone! Check Revit to verify wall placement.")
    return len(created_walls) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
