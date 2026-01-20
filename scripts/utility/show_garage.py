#!/usr/bin/env python3
"""
Show garage location and create a room inside it.
Garage 101 is located at:
- X: 0' to 12' (west side of building)
- Y: 0' to 20' (from front to just past middle)
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
        max_attempts = 50
        for attempt in range(max_attempts):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                time.sleep(0.02)
                continue
            except Exception:
                time.sleep(0.02)
                continue

        win32file.CloseHandle(handle)
        return {"success": False, "error": f"Response incomplete: {len(response_data)} bytes"}
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running"}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("GARAGE LOCATION - Room 101")
print("=" * 80)

# Get active view
print("\n1. Getting active view...")
result = send_mcp_request("getActiveView", {})
if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    sys.exit(1)

view_id = result.get("viewId")
print(f"   View: {result.get('viewName')} (ID: {view_id})")

# Garage boundaries
GARAGE = {
    "name": "GARAGE",
    "number": "101",
    "min_x": 0,
    "max_x": 12,
    "min_y": 0,
    "max_y": 20,
    "center_x": 6,
    "center_y": 10
}

print(f"\n2. Garage Location:")
print(f"   Southwest corner: (0', 0')")
print(f"   Northeast corner: (12', 20')")
print(f"   Size: 12' wide x 20' deep = 240 sq ft")
print(f"   Center point: ({GARAGE['center_x']}', {GARAGE['center_y']}')")

# Draw a box around the garage with detail lines
print("\n3. Drawing garage outline...")

garage_outline = [
    {"name": "Garage South", "start": [0, 0], "end": [12, 0]},
    {"name": "Garage East", "start": [12, 0], "end": [12, 20]},
    {"name": "Garage North", "start": [12, 20], "end": [0, 20]},
    {"name": "Garage West", "start": [0, 20], "end": [0, 0]},
]

for line in garage_outline:
    result = send_mcp_request("createDetailLine", {
        "viewId": view_id,
        "startPoint": line["start"] + [0],
        "endPoint": line["end"] + [0]
    })
    status = "[OK]" if result.get("success") else "[FAIL]"
    print(f"   {status} {line['name']}")

# Create room in the garage
print("\n4. Creating room in garage space...")

# First check if createRoom method exists
result = send_mcp_request("createRoom", {
    "levelId": 30,  # L1 level
    "point": [GARAGE["center_x"], GARAGE["center_y"], 0],
    "name": "GARAGE",
    "number": "101"
})

if result.get("success"):
    print(f"   [OK] Room created: {result.get('roomId')}")
else:
    print(f"   Room creation: {result.get('error')}")

    # Try placing a room tag instead
    print("\n   Trying to place room tag...")
    result = send_mcp_request("placeRoomTag", {
        "viewId": view_id,
        "point": [GARAGE["center_x"], GARAGE["center_y"], 0]
    })

    if result.get("success"):
        print(f"   [OK] Room tag placed")
    else:
        print(f"   Room tag: {result.get('error')}")

# Add a prominent text label
print("\n5. Adding garage label...")

result = send_mcp_request("createTextNote", {
    "viewId": view_id,
    "position": [GARAGE["center_x"], GARAGE["center_y"], 0],
    "text": "GARAGE\n101\n(12' x 20')"
})

if result.get("success"):
    print(f"   [OK] Label placed at center of garage")
else:
    print(f"   [FAIL] {result.get('error')}")

# Draw diagonal lines to mark the garage clearly
print("\n6. Drawing X marker in garage...")

# Diagonal from SW to NE
result = send_mcp_request("createDetailLine", {
    "viewId": view_id,
    "startPoint": [1, 1, 0],
    "endPoint": [11, 19, 0]
})
print(f"   Diagonal 1: {'[OK]' if result.get('success') else '[FAIL]'}")

# Diagonal from NW to SE
result = send_mcp_request("createDetailLine", {
    "viewId": view_id,
    "startPoint": [1, 19, 0],
    "endPoint": [11, 1, 0]
})
print(f"   Diagonal 2: {'[OK]' if result.get('success') else '[FAIL]'}")

print("\n" + "=" * 80)
print("GARAGE LOCATION SUMMARY")
print("=" * 80)
print("""
The GARAGE (Room 101) is located in the SOUTHWEST corner of the building:

Building Layout (looking from above, North is up):

                    NORTH (Y = 28.67')
        +------------------------------------------+
        |   KITCHEN    |      REAR LANAI           |
        |     104      |                           |
  W     +------+-------+---------------------------+ E
  E     | UTIL | PNTR  |                           | A
  S     | 102  | 103   |      LIVING RM 105        | S
  T     +------+-------+                           | T
        |              |                           |
        |   GARAGE     +---------------------------+
        |     101      |  STAIRS  |                |
        |              |   108    |  DINING 106    |
        | [X MARKER]   +----+-----+                |
        |              |BATH|FOYER|                |
        |              |107 | 109 |                |
        +--------------+----+-----+----------------+
                    SOUTH (Y = 0')
        X=0          X=12  X=16  X=22           X=45.33'

GARAGE 101:
  - Position: Southwest corner
  - X: 0' to 12'
  - Y: 0' to 20'
  - Size: 12' x 20' = 240 sq ft
  - Bounded by: West exterior wall, South exterior wall,
                Garage East partition wall, Kitchen/Utility walls
""")
print("=" * 80)
