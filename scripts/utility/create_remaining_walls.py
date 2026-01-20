#!/usr/bin/env python3
"""
Create the remaining interior walls that failed in the previous run.
These walls need to be created to complete the floor plan.
"""

import json
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, params):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        request = {"method": method, "params": params}
        request_json = json.dumps(request) + "\n"
        win32file.WriteFile(handle, request_json.encode('utf-8'))
        result, data = win32file.ReadFile(handle, 64 * 1024)
        win32file.CloseHandle(handle)
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        return {"success": False, "error": str(e)}

# Get level
print("Getting level...")
result = send_mcp_request("getLevels", {})
if not result.get("success"):
    print(f"ERROR: {result.get('error')}")
    sys.exit(1)

level_id = None
for level in result.get("levels", []):
    if "l1" in level.get("name", "").lower() or "first" in level.get("name", "").lower():
        level_id = level.get("levelId")
        break
if not level_id:
    level_id = result.get("levels", [{}])[0].get("levelId")
print(f"Using level ID: {level_id}")

WALL_HEIGHT = 10.0

# Walls that failed previously - need to create these
remaining_walls = [
    # Garage East Wall - this is critical, separates garage from house
    {"start": [12.0, 0, 0], "end": [12.0, 20.0, 0], "name": "Garage East Wall"},

    # 1/2 Bath walls
    {"start": [16.0, 0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath East Wall"},
    {"start": [12.0, 6.0, 0], "end": [16.0, 6.0, 0], "name": "1/2 Bath North Wall"},

    # Foyer/Stairs area
    {"start": [12.0, 10.0, 0], "end": [22.0, 10.0, 0], "name": "Foyer North Wall"},
    {"start": [16.0, 6.0, 0], "end": [16.0, 10.0, 0], "name": "Closet/Stairs West Wall"},

    # Living/Dining divider
    {"start": [22.0, 10.0, 0], "end": [22.0, 20.0, 0], "name": "Living/Dining Divider"},
]

print(f"\nCreating {len(remaining_walls)} remaining walls...")

for wall_def in remaining_walls:
    result = send_mcp_request("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": level_id,
        "height": WALL_HEIGHT
    })
    if result.get("success"):
        print(f"  [OK] {wall_def['name']} (ID: {result.get('wallId')})")
    else:
        print(f"  [FAIL] {wall_def['name']}: {result.get('error')}")

print("\nDone!")
