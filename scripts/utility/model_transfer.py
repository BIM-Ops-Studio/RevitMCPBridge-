#!/usr/bin/env python3
"""
Model Transfer Script - Transfer model data from 512 Clematis to MFI Project
This script extracts data from source and creates elements in target
"""

import json
import time
import sys
import os

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_request(method, parameters=None):
    """Send a request to the MCP server and return the response"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )

        request = {"method": method, "parameters": parameters or {}}
        win32file.WriteFile(handle, json.dumps(request).encode('utf-8'))
        result, data = win32file.ReadFile(handle, 256 * 1024)  # 256KB buffer
        win32file.CloseHandle(handle)

        return json.loads(data.decode('utf-8'))
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running"}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_json(data, filename):
    """Save data to JSON file"""
    filepath = os.path.join(os.path.dirname(__file__), 'transfer_data', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {filepath}")
    return filepath

def load_json(filename):
    """Load data from JSON file"""
    filepath = os.path.join(os.path.dirname(__file__), 'transfer_data', filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

# ============================================================================
# PHASE 1: Extract from Source (512 Clematis)
# ============================================================================
def extract_source_data():
    """Extract all data from the source project (512 Clematis)"""
    print_header("PHASE 1: EXTRACTING DATA FROM SOURCE PROJECT")

    # Get project info
    print("\n1. Getting project info...")
    info = send_request("getProjectInfo", {})
    if info.get("success"):
        project_name = info.get("projectName", "Unknown")
        print(f"  Active Project: {project_name}")
        if "512" not in project_name.lower() and "clematis" not in project_name.lower():
            print("\n  WARNING: This doesn't look like 512 Clematis!")
            print("  Please make sure 512 Clematis is the active project in Revit.")
            return False
    else:
        print(f"  ERROR: {info.get('error')}")
        return False

    # Get levels
    print("\n2. Extracting levels...")
    levels = send_request("getLevels", {})
    if levels.get("success"):
        level_list = levels.get("levels", [])
        print(f"  Found {len(level_list)} levels")
        save_json(level_list, "source_levels.json")
        for lvl in level_list:
            print(f"    - {lvl.get('name')}: {lvl.get('elevation')}'")
    else:
        print(f"  ERROR: {levels.get('error')}")

    # Get wall types
    print("\n3. Extracting wall types...")
    wall_types = send_request("getWallTypes", {})
    if wall_types.get("success"):
        types = wall_types.get("wallTypes", [])
        print(f"  Found {len(types)} wall types")
        save_json(types, "source_wall_types.json")
    else:
        print(f"  ERROR: {wall_types.get('error')}")

    # Get door types
    print("\n4. Extracting door types...")
    door_types = send_request("getDoorTypes", {})
    if door_types.get("success"):
        types = door_types.get("doorTypes", [])
        print(f"  Found {len(types)} door types")
        save_json(types, "source_door_types.json")
    else:
        print(f"  ERROR: {door_types.get('error')}")

    # Get window types
    print("\n5. Extracting window types...")
    window_types = send_request("getWindowTypes", {})
    if window_types.get("success"):
        types = window_types.get("windowTypes", [])
        print(f"  Found {len(types)} window types")
        save_json(types, "source_window_types.json")
    else:
        print(f"  ERROR: {window_types.get('error')}")

    # Get family types by category
    print("\n6. Extracting family types by category...")
    categories = [
        ("Plumbing Fixtures", "plumbing_fixtures"),
        ("Lighting Fixtures", "lighting_fixtures"),
        ("Electrical Fixtures", "electrical_fixtures"),
        ("Furniture", "furniture"),
        ("Casework", "casework"),
        ("Specialty Equipment", "specialty_equipment"),
        ("Curtain Panels", "curtain_panels"),
        ("Railings", "railings")
    ]

    for cat_name, file_prefix in categories:
        types = send_request("getFamilyTypesByCategory", {"category": cat_name})
        if types.get("success"):
            type_list = types.get("familyTypes", [])
            if type_list:
                print(f"  {cat_name}: {len(type_list)} types")
                save_json(type_list, f"source_{file_prefix}.json")
        else:
            print(f"  {cat_name}: Error - {types.get('error', 'Unknown')}")

    # Get walls
    print("\n7. Extracting walls...")
    walls = send_request("getAllWalls", {})
    if walls.get("success"):
        wall_list = walls.get("walls", [])
        print(f"  Found {len(wall_list)} walls")
        save_json(wall_list, "source_walls.json")
    else:
        print(f"  ERROR: {walls.get('error')}")

    # Get floors
    print("\n8. Extracting floors...")
    floors = send_request("getFloors", {})
    if floors.get("success"):
        floor_list = floors.get("floors", [])
        print(f"  Found {len(floor_list)} floors")
        save_json(floor_list, "source_floors.json")
    else:
        print(f"  Note: {floors.get('error')}")

    # Get rooms
    print("\n9. Extracting rooms...")
    rooms = send_request("getRooms", {})
    if rooms.get("success"):
        room_list = rooms.get("rooms", [])
        print(f"  Found {len(room_list)} rooms")
        save_json(room_list, "source_rooms.json")
    else:
        print(f"  Note: {rooms.get('error')}")

    print("\n" + "=" * 80)
    print("  EXTRACTION COMPLETE!")
    print("  Data saved to transfer_data/ folder")
    print("=" * 80)

    return True

# ============================================================================
# PHASE 2: Create in Target (MFI Project)
# ============================================================================
def create_in_target():
    """Create elements in the target project (MFI Project)"""
    print_header("PHASE 2: CREATING IN TARGET PROJECT")

    # Get project info
    print("\n1. Verifying target project...")
    info = send_request("getProjectInfo", {})
    if info.get("success"):
        project_name = info.get("projectName", "Unknown")
        print(f"  Active Project: {project_name}")
        if "mfi" not in project_name.lower() and "test" not in project_name.lower():
            print("\n  WARNING: This doesn't look like the MFI test project!")
            print("  Please make sure MFI Project is the active project in Revit.")
            resp = input("  Continue anyway? (y/n): ")
            if resp.lower() != 'y':
                return False
    else:
        print(f"  ERROR: {info.get('error')}")
        return False

    # Create levels
    print("\n2. Creating levels...")
    try:
        source_levels = load_json("source_levels.json")
        for lvl in source_levels:
            result = send_request("createLevel", {
                "name": lvl.get("name"),
                "elevation": lvl.get("elevation")
            })
            if result.get("success"):
                print(f"  Created: {lvl.get('name')} at {lvl.get('elevation')}'")
            else:
                print(f"  Note: {lvl.get('name')} - {result.get('error')}")
            time.sleep(0.1)  # Small delay between operations
    except FileNotFoundError:
        print("  ERROR: source_levels.json not found. Run extraction first.")

    # Load wall types (using transfer project standards or loading families)
    print("\n3. Loading wall types...")
    print("  Note: Wall types require Transfer Project Standards in Revit UI")
    print("  or loading specific wall families.")

    # Load families from source data
    print("\n4. Loading family types...")
    family_files = [
        ("source_door_types.json", "Doors"),
        ("source_window_types.json", "Windows"),
        ("source_plumbing_fixtures.json", "Plumbing Fixtures"),
        ("source_lighting_fixtures.json", "Lighting Fixtures"),
        ("source_furniture.json", "Furniture"),
        ("source_casework.json", "Casework")
    ]

    for filename, category in family_files:
        try:
            types = load_json(filename)
            print(f"  {category}: {len(types)} types to transfer")
            # Note: Actual loading requires family file paths or Transfer Project Standards
        except FileNotFoundError:
            pass

    # Create walls from source data
    print("\n5. Creating walls...")
    try:
        source_walls = load_json("source_walls.json")
        created = 0
        failed = 0

        for i, wall in enumerate(source_walls[:20]):  # Limit to first 20 for testing
            result = send_request("createWall", {
                "startPoint": wall.get("startPoint"),
                "endPoint": wall.get("endPoint"),
                "levelId": wall.get("levelId"),
                "height": wall.get("height", 10),
                "wallTypeId": wall.get("wallTypeId")
            })

            if result.get("success"):
                created += 1
            else:
                failed += 1

            if (i + 1) % 5 == 0:
                print(f"  Progress: {i + 1}/{len(source_walls[:20])} walls")
            time.sleep(0.1)

        print(f"  Created: {created} walls")
        print(f"  Failed: {failed} walls")

    except FileNotFoundError:
        print("  ERROR: source_walls.json not found. Run extraction first.")

    print("\n" + "=" * 80)
    print("  TARGET CREATION COMPLETE!")
    print("=" * 80)

    return True

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  MODEL TRANSFER: 512 Clematis -> MFI Project")
    print("=" * 80)

    print("\nThis script has two phases:")
    print("  1. Extract data from 512 Clematis (make it active first)")
    print("  2. Create elements in MFI Project (make it active first)")

    if len(sys.argv) > 1:
        if sys.argv[1] == "extract":
            extract_source_data()
        elif sys.argv[1] == "create":
            create_in_target()
        else:
            print(f"\nUnknown command: {sys.argv[1]}")
            print("Usage: python model_transfer.py [extract|create]")
    else:
        print("\nUsage:")
        print("  python model_transfer.py extract  - Extract from 512 Clematis")
        print("  python model_transfer.py create   - Create in MFI Project")
        print("\nInteractive mode:")

        choice = input("\nChoose action:\n  1. Extract from source (512 Clematis)\n  2. Create in target (MFI Project)\n  Enter (1 or 2): ")

        if choice == "1":
            extract_source_data()
        elif choice == "2":
            create_in_target()
        else:
            print("Invalid choice")
