#!/usr/bin/env python3
"""Get active view and draw room diagram on it."""

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
print("GET ACTIVE VIEW & CREATE ROOM DIAGRAM")
print("=" * 80)

# Get active view
print("\n1. Getting active view...")
result = send_mcp_request("getActiveView", {})

if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    print("\n   Trying to get all views instead...")

    result = send_mcp_request("getAllViews", {})
    if result.get("success"):
        views = result.get("views", [])
        print(f"   Found {len(views)} views")
        for v in views[:20]:
            print(f"     {v.get('viewId')}: {v.get('name')} ({v.get('viewType')})")
    else:
        print(f"   ERROR: {result.get('error')}")
    sys.exit(1)

view_id = result.get("viewId")
view_name = result.get("viewName", result.get("name", "Unknown"))
view_type = result.get("viewType", "Unknown")

print(f"   Active View: {view_name}")
print(f"   Type: {view_type}")
print(f"   ID: {view_id}")

# ============================================================================
# Draw Room Labels and Markers
# ============================================================================
print("\n2. Drawing room diagram on active view...")

# Room definitions with label positions (X, Y in feet from origin)
rooms = [
    {"name": "GARAGE 101", "x": 6, "y": 10},
    {"name": "UTILITY 102", "x": 4, "y": 8.5},
    {"name": "PANTRY 103", "x": 10, "y": 8.5},
    {"name": "KITCHEN 104", "x": 6, "y": 24},
    {"name": "LIVING RM 105", "x": 33, "y": 15},
    {"name": "DINING RM 106", "x": 33, "y": 5},
    {"name": "1/2 BATH 107", "x": 14, "y": 3},
    {"name": "STAIRS 108", "x": 19, "y": 8},
    {"name": "FOYER 109", "x": 17, "y": 2},
    {"name": "REAR LANAI", "x": 28, "y": 24},
]

labels_created = 0
labels_failed = 0

for room in rooms:
    result = send_mcp_request("createTextNote", {
        "viewId": view_id,
        "position": [room["x"], room["y"], 0],
        "text": room["name"]
    })

    if result.get("success"):
        labels_created += 1
        print(f"   [OK] {room['name']} at ({room['x']}, {room['y']})")
    else:
        labels_failed += 1
        print(f"   [FAIL] {room['name']}: {result.get('error')}")

# ============================================================================
# Draw Boundary Lines
# ============================================================================
print("\n3. Drawing room boundary lines...")

# Key boundary lines to show room divisions
boundaries = [
    # Garage boundary
    {"name": "Garage East", "start": [12, 0], "end": [12, 20]},
    {"name": "Garage North", "start": [0, 20], "end": [12, 20]},

    # Bath/Foyer division
    {"name": "Bath East", "start": [16, 0], "end": [16, 6]},
    {"name": "Bath North", "start": [12, 6], "end": [16, 6]},

    # Stairs area
    {"name": "Stairs South", "start": [12, 10], "end": [22, 10]},
    {"name": "Stairs West", "start": [16, 6], "end": [16, 10]},

    # Living/Dining
    {"name": "Living South", "start": [22, 10], "end": [22, 20]},

    # Lanai
    {"name": "Lanai South", "start": [12, 20], "end": [45.333, 20]},

    # Building perimeter
    {"name": "South Wall", "start": [0, 0], "end": [45.333, 0]},
    {"name": "East Wall", "start": [45.333, 0], "end": [45.333, 28.667]},
    {"name": "North Wall", "start": [45.333, 28.667], "end": [0, 28.667]},
    {"name": "West Wall", "start": [0, 28.667], "end": [0, 0]},
]

lines_created = 0
lines_failed = 0

for line in boundaries:
    result = send_mcp_request("createDetailLine", {
        "viewId": view_id,
        "startPoint": line["start"] + [0],  # Add Z=0
        "endPoint": line["end"] + [0]
    })

    if result.get("success"):
        lines_created += 1
        print(f"   [OK] {line['name']}")
    else:
        lines_failed += 1
        print(f"   [FAIL] {line['name']}: {result.get('error')}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"   View: {view_name} (ID: {view_id})")
print(f"   Labels created: {labels_created}/{len(rooms)}")
print(f"   Lines created: {lines_created}/{len(boundaries)}")
print("\nCheck the view in Revit to see the room diagram!")
print("=" * 80)
