"""
FIX: Create walls without specifying wallTypeId - let Revit use default
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
print("CREATING WALLS (using default wall type)")
print("=" * 70)

# Get Level 1 ID
print("\nGetting Level 1...")
result = call_mcp("getLevels")
level1_id = None
if result.get("success"):
    levels = result.get("result", {}).get("levels", [])
    for lvl in levels:
        if "level 1" in lvl.get("name", "").lower() or abs(lvl.get("elevation", -1)) < 0.1:
            level1_id = lvl.get("levelId")
            print(f"   Found Level 1: ID {level1_id}")
            break

if not level1_id:
    print("   ERROR: Level 1 not found!")
    exit(1)

WALL_HEIGHT = 10.0

# Exterior walls - simplified rectangle for testing
exterior_walls = [
    {"name": "South Wall", "start": [0, 0, 0], "end": [38, 0, 0]},
    {"name": "East Wall", "start": [38, 0, 0], "end": [38, 30, 0]},
    {"name": "North Wall", "start": [38, 30, 0], "end": [0, 30, 0]},
    {"name": "West Wall", "start": [0, 30, 0], "end": [0, 0, 0]},
]

wall_ids = []
print("\nCreating exterior walls (NO wallTypeId - use default)...")

for wall_def in exterior_walls:
    print(f"   Creating {wall_def['name']}...")

    # Don't pass wallTypeId - let WallMethods use default
    result = call_mcp("createWallByPoints", {
        "startPoint": wall_def["start"],
        "endPoint": wall_def["end"],
        "levelId": level1_id,
        "height": WALL_HEIGHT
        # No wallTypeId - will use first available basic wall type
    })

    if result.get("success"):
        wall_id = result.get("wallId")
        wall_ids.append(wall_id)
        print(f"      OK - Wall ID: {wall_id}")
    else:
        print(f"      FAIL - {result.get('error')}")

print(f"\nTotal walls created: {len(wall_ids)}")

if wall_ids:
    print("\nSUCCESS! Check Revit - you should see a 38' x 30' rectangular room.")
else:
    print("\nFailed to create walls. The blank project may need a template with wall types.")
