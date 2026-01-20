"""
Build 1st Floor Shell from PDF Construction Documents
Riviera Beach 2-Story Residence - Lot #673 West 1st Street

This script creates the basic building shell (exterior walls, doors, windows)
from the PDF floor plan analysis.
"""

import win32file
import json
import time

def send_mcp_command(method, parameters):
    """Send command to Revit MCP Bridge"""
    try:
        h = win32file.CreateFile(
            r'\\.\pipe\RevitMCPBridge2026',
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        request = (json.dumps({"method": method, "parameters": parameters}) + "\n").encode()
        win32file.WriteFile(h, request)

        _, data = win32file.ReadFile(h, 64*1024)
        win32file.CloseHandle(h)

        result = json.loads(data.decode())
        return result
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

def main():
    print("="*80)
    print("BUILDING 1ST FLOOR SHELL FROM PDF")
    print("Project: Riviera Beach 2-Story Prototype")
    print("="*80)

    # Step 1: Get levels to confirm First Floor level exists
    print("\n[1/5] Checking levels...")
    levels_result = send_mcp_command("getLevels", {})

    if not levels_result.get("success"):
        print(f"ERROR: Could not get levels: {levels_result.get('error')}")
        return

    levels = levels_result.get("levels", [])
    first_floor_level = None

    for level in levels:
        if "first" in level.get("name", "").lower() or level.get("elevation") == 0.0:
            first_floor_level = level
            break

    if not first_floor_level:
        print("ERROR: Could not find First Floor level")
        print(f"Available levels: {[l.get('name') for l in levels]}")
        return

    print(f"[OK] Found level: {first_floor_level.get('name')} @ {first_floor_level.get('elevation')}'")
    level_id = first_floor_level.get("id")

    # Step 2: Get available wall types
    print("\n[2/5] Getting wall types...")
    wall_types_result = send_mcp_command("getWallTypes", {})

    if not wall_types_result.get("success"):
        print(f"ERROR: Could not get wall types: {wall_types_result.get('error')}")
        return

    wall_types = wall_types_result.get("wallTypes", [])
    if not wall_types:
        print("ERROR: No wall types available")
        return

    # Use the first available wall type for testing
    wall_type = wall_types[0]
    wall_type_id = wall_type.get("id")
    print(f"[OK] Using wall type: {wall_type.get('name')} (ID: {wall_type_id})")

    # Step 3: Create exterior walls
    # Building dimensions from PDF: 45'-4" x 28'-8"
    # Converting to decimal feet: 45.333' x 28.667'

    print("\n[3/6] Creating exterior walls...")
    print("Building footprint: 45'-4\" x 28'-8\"")

    # Wall coordinates (clockwise from SW corner at origin 0,0)
    # Using simplified rectangular footprint for initial test

    walls_data = [
        # South wall (front) - along X axis
        {
            "start": {"x": 0, "y": 0, "z": 0},
            "end": {"x": 45.333, "y": 0, "z": 0},
            "height": 10.5,
            "levelId": level_id,
            "description": "South exterior wall (front)"
        },
        # East wall (right) - along Y axis
        {
            "start": {"x": 45.333, "y": 0, "z": 0},
            "end": {"x": 45.333, "y": 28.667, "z": 0},
            "height": 10.5,
            "levelId": level_id,
            "description": "East exterior wall"
        },
        # North wall (back)
        {
            "start": {"x": 45.333, "y": 28.667, "z": 0},
            "end": {"x": 0, "y": 28.667, "z": 0},
            "height": 10.5,
            "levelId": level_id,
            "description": "North exterior wall (back)"
        },
        # West wall (left)
        {
            "start": {"x": 0, "y": 28.667, "z": 0},
            "end": {"x": 0, "y": 0, "z": 0},
            "height": 10.5,
            "levelId": level_id,
            "description": "West exterior wall"
        }
    ]

    created_walls = []

    for i, wall_data in enumerate(walls_data):
        print(f"  Creating {wall_data['description']}...")

        result = send_mcp_command("createWall", {
            "startPoint": wall_data["start"],
            "endPoint": wall_data["end"],
            "levelId": level_id,
            "wallTypeId": wall_type_id,
            "height": wall_data["height"],
            "offset": 0
        })

        if result.get("success"):
            wall_id = result.get("wallId")
            created_walls.append({"id": wall_id, "data": wall_data})
            print(f"    [OK] Created wall ID: {wall_id}")
        else:
            print(f"    [FAILED] {result.get('error')}")

        time.sleep(0.2)  # Small delay between commands

    print(f"\n[OK] Created {len(created_walls)} exterior walls")

    # Step 4: Doors (simplified - main entry only for test)
    print("\n[4/6] Placing exterior doors...")

    # Front entry door (Door 109 - D2 type, 3'-0" wide)
    # Location: approximately center of south wall
    # From plan: appears to be around X=21' (roughly centered)

    doors_data = [
        {
            "location": {"x": 21.0, "y": 0, "z": 0},  # South wall, roughly centered
            "name": "Front Entry (D2)",
            "width": 3.0,
            "height": 6.667  # 6'-8" per schedule
        }
    ]

    print(f"  Note: Placing {len(doors_data)} door(s) for initial test")
    print("  (Full door placement will follow after verification)")

    # Step 5: Windows (simplified - a few windows for test)
    print("\n[5/6] Placing windows...")
    print("  Note: Window placement deferred to next phase")
    print("  (Will add after wall verification)")

    # Step 6: Summary
    print("\n" + "="*80)
    print("BUILD SUMMARY")
    print("="*80)
    print(f"Level used: {first_floor_level.get('name')}")
    print(f"Walls created: {len(created_walls)}")
    print(f"Building footprint: 45'-4\" x 28'-8\" (45.333' x 28.667')")
    print(f"\nNext steps:")
    print("  1. Verify walls in Revit 3D view")
    print("  2. Check wall alignment and closure")
    print("  3. Add doors to walls")
    print("  4. Add windows to walls")
    print("  5. Refine geometry (garage projection, porches)")
    print("="*80)

if __name__ == "__main__":
    main()
