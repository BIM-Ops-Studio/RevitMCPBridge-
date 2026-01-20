"""
Create walls directly using known Level 1 ID
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
print("CREATING WALLS")
print("=" * 70)

# Use Level 1 ID directly
LEVEL1_ID = 1240472
WALL_HEIGHT = 10.0

print(f"\nUsing Level 1 ID: {LEVEL1_ID}")

# Simple rectangular house: 38' x 30'
walls = [
    {"name": "South Wall", "start": [0, 0, 0], "end": [38, 0, 0]},
    {"name": "East Wall", "start": [38, 0, 0], "end": [38, 30, 0]},
    {"name": "North Wall", "start": [38, 30, 0], "end": [0, 30, 0]},
    {"name": "West Wall", "start": [0, 30, 0], "end": [0, 0, 0]},
]

wall_ids = []
print("\nCreating walls...")

for wall_def in walls:
    print(f"   Creating {wall_def['name']}...")

    result = call_mcp("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": LEVEL1_ID,
        "height": WALL_HEIGHT
    })

    if result.get("success"):
        wall_id = result.get("wallId")
        wall_ids.append(wall_id)
        print(f"      OK - Wall ID: {wall_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\nTotal walls created: {len(wall_ids)}")

if wall_ids:
    # Now add some interior walls
    print("\nCreating interior walls...")

    interior_walls = [
        {"name": "Living/Kitchen divider", "start": [20, 0, 0], "end": [20, 18, 0]},
        {"name": "Bedroom wall", "start": [8, 10, 0], "end": [8, 30, 0]},
        {"name": "Hallway wall", "start": [8, 10, 0], "end": [20, 10, 0]},
    ]

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
            wall_ids.append(wall_id)
            print(f"      OK - Wall ID: {wall_id}")
        else:
            print(f"      FAIL - {result.get('error')}")

    print(f"\nTotal walls created: {len(wall_ids)}")

    # Now let's add a door
    print("\nPlacing front door...")
    result = call_mcp("placeDoor", {
        "wallId": wall_ids[0],  # South wall
        "location": [19, 0, 0]
    })
    if result.get("success"):
        print(f"   OK - Door ID: {result.get('doorId')}")
    else:
        print(f"   FAIL - {result.get('error')}")

print("\n" + "=" * 70)
print("Check Revit - you should see walls!")
print("=" * 70)
