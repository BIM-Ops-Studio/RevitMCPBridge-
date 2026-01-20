#!/usr/bin/env python3
"""
Debug: Query what walls ACTUALLY exist in Revit right now.
Get their exact coordinates to see what we're working with.
"""

import json
import sys
import time

try:
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

        response_data = b""
        for _ in range(100):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                time.sleep(0.05)
                continue
        win32file.CloseHandle(handle)
        return {"success": False, "error": "Response incomplete"}
    except pywintypes.error as e:
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("DEBUG: ACTUAL WALLS IN REVIT")
print("=" * 80)

# Get all walls
print("\n1. Querying all walls...")
result = send_mcp_request("getWalls", {})

if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    sys.exit(1)

walls = result.get("walls", [])
print(f"   Found {len(walls)} walls")

# Print each wall's actual coordinates
print("\n2. Wall Details:")
print("-" * 80)

for i, wall in enumerate(walls):
    wall_id = wall.get("wallId", "?")
    wall_type = wall.get("wallTypeName", "Unknown")

    # Get location data
    start = wall.get("startPoint", {})
    end = wall.get("endPoint", {})
    length = wall.get("length", 0)

    start_x = start.get("x", 0) if isinstance(start, dict) else 0
    start_y = start.get("y", 0) if isinstance(start, dict) else 0
    end_x = end.get("x", 0) if isinstance(end, dict) else 0
    end_y = end.get("y", 0) if isinstance(end, dict) else 0

    # Determine wall orientation
    if abs(start_x - end_x) < 0.1:
        orientation = "VERTICAL (N-S)"
        position = f"X = {start_x:.2f}'"
    elif abs(start_y - end_y) < 0.1:
        orientation = "HORIZONTAL (E-W)"
        position = f"Y = {start_y:.2f}'"
    else:
        orientation = "DIAGONAL"
        position = f"({start_x:.2f},{start_y:.2f}) to ({end_x:.2f},{end_y:.2f})"

    print(f"\nWall {i+1} (ID: {wall_id})")
    print(f"   Type: {wall_type}")
    print(f"   Start: ({start_x:.2f}', {start_y:.2f}')")
    print(f"   End:   ({end_x:.2f}', {end_y:.2f}')")
    print(f"   Length: {length:.2f}'")
    print(f"   Orientation: {orientation}")
    print(f"   Position: {position}")

# Summarize the bounding box
print("\n" + "=" * 80)
print("3. BOUNDING BOX ANALYSIS")
print("=" * 80)

all_x = []
all_y = []

for wall in walls:
    start = wall.get("startPoint", {})
    end = wall.get("endPoint", {})
    if isinstance(start, dict):
        all_x.extend([start.get("x", 0), end.get("x", 0)])
        all_y.extend([start.get("y", 0), end.get("y", 0)])

if all_x and all_y:
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x
    depth = max_y - min_y

    print(f"\n   X Range: {min_x:.2f}' to {max_x:.2f}' (Width: {width:.2f}')")
    print(f"   Y Range: {min_y:.2f}' to {max_y:.2f}' (Depth: {depth:.2f}')")

    print(f"\n   EXPECTED from PDF A-100:")
    print(f"   X Range: 0' to 45.33' (Width: 45.33')")
    print(f"   Y Range: 0' to 28.67' (Depth: 28.67')")

    if abs(width - 45.33) < 1 and abs(depth - 28.67) < 1:
        print("\n   [OK] Building envelope matches PDF!")
    else:
        print(f"\n   [MISMATCH] Building envelope does NOT match PDF!")
        print(f"   Width difference: {width - 45.33:.2f}'")
        print(f"   Depth difference: {depth - 28.67:.2f}'")

print("\n" + "=" * 80)
print("4. EXPECTED INTERIOR WALLS FROM PDF A-100")
print("=" * 80)
print("""
Key interior walls that should exist:

1. GARAGE EAST WALL: X = 12' (vertical, from Y=0 to Y=20)
   - Separates garage from rest of house

2. KITCHEN SOUTH WALL: Y = 20' (horizontal, from X=0 to X=12)
   - Separates kitchen from utility/pantry area

3. UTILITY/PANTRY DIVIDER: X = 8' (vertical, from Y=7 to Y=10)
   - Separates utility room from pantry

4. BATH EAST WALL: X = 16' (vertical, from Y=0 to Y=6)
   - East wall of 1/2 bath

5. BATH NORTH WALL: Y = 6' (horizontal, from X=12 to X=16)
   - North wall of 1/2 bath

6. FOYER/CLOSET NORTH WALL: Y = 10' (horizontal, from X=12 to X=22)
   - North wall of foyer/closet area

7. LIVING/DINING DIVIDER: X = 22' (vertical, from Y=10 to Y=20)
   - Separates living room from dining room

8. LANAI SOUTH WALL: Y = 20' (horizontal, from X=12 to X=45.33)
   - South edge of rear lanai
""")

print("=" * 80)
