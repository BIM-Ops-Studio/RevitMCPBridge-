#!/usr/bin/env python3
"""
Draw room diagram with sketch lines and room labels on the floor plan.
This creates an architect-style sketch overlay showing room boundaries and names.
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
print("DRAW ROOM DIAGRAM - ARCHITECT SKETCH STYLE")
print("=" * 80)

# ============================================================================
# STEP 1: Get Floor Plan View
# ============================================================================
print("\n1. Finding floor plan view...")

result = send_mcp_request("getViews", {})
if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    sys.exit(1)

views = result.get("views", [])
floor_plan_view_id = None

# Look for a floor plan view
for view in views:
    view_type = view.get("viewType", "").lower()
    name = view.get("name", "").lower()

    if "floorplan" in view_type or "floor plan" in view_type:
        # Prefer "L1" or "First Floor" or "Level 1"
        if "l1" in name or "first" in name or "level 1" in name:
            floor_plan_view_id = view.get("viewId")
            print(f"   Found: {view.get('name')} (ID: {floor_plan_view_id})")
            break

# If no specific level found, use any floor plan
if not floor_plan_view_id:
    for view in views:
        view_type = view.get("viewType", "").lower()
        if "floorplan" in view_type or "floor plan" in view_type:
            floor_plan_view_id = view.get("viewId")
            print(f"   Using: {view.get('name')} (ID: {floor_plan_view_id})")
            break

if not floor_plan_view_id:
    print("   ERROR: No floor plan view found!")
    print("   Available views:")
    for v in views[:10]:
        print(f"     - {v.get('name')} ({v.get('viewType')})")
    sys.exit(1)

# ============================================================================
# STEP 2: Room Definitions from A-100
# ============================================================================
print("\n2. Defining rooms from A-100 floor plan...")

# Room definitions with boundaries and label positions
# Format: name, boundaries (list of line segments), label position (center of room)
rooms = [
    {
        "name": "GARAGE\n101",
        "number": "101",
        "bounds": {
            "min_x": 0,
            "max_x": 12,
            "min_y": 0,
            "max_y": 20
        },
        "label_pos": [6, 10]  # Center of garage
    },
    {
        "name": "UTILITY\n102",
        "number": "102",
        "bounds": {
            "min_x": 0,
            "max_x": 8,
            "min_y": 7,
            "max_y": 10
        },
        "label_pos": [4, 8.5]
    },
    {
        "name": "PANTRY\n103",
        "number": "103",
        "bounds": {
            "min_x": 8,
            "max_x": 12,
            "min_y": 7,
            "max_y": 10
        },
        "label_pos": [10, 8.5]
    },
    {
        "name": "KITCHEN\n104",
        "number": "104",
        "bounds": {
            "min_x": 0,
            "max_x": 12,
            "min_y": 20,
            "max_y": 28.667
        },
        "label_pos": [6, 24]
    },
    {
        "name": "LIVING RM\n105",
        "number": "105",
        "bounds": {
            "min_x": 22,
            "max_x": 45.333,
            "min_y": 10,
            "max_y": 20
        },
        "label_pos": [33.5, 15]
    },
    {
        "name": "DINING RM\n106",
        "number": "106",
        "bounds": {
            "min_x": 22,
            "max_x": 45.333,
            "min_y": 0,
            "max_y": 10
        },
        "label_pos": [33.5, 5]
    },
    {
        "name": "1/2 BATH\n107",
        "number": "107",
        "bounds": {
            "min_x": 12,
            "max_x": 16,
            "min_y": 0,
            "max_y": 6
        },
        "label_pos": [14, 3]
    },
    {
        "name": "CLOSET/\nSTAIRS\n108",
        "number": "108",
        "bounds": {
            "min_x": 16,
            "max_x": 22,
            "min_y": 6,
            "max_y": 10
        },
        "label_pos": [19, 8]
    },
    {
        "name": "FOYER\n109",
        "number": "109",
        "bounds": {
            "min_x": 12,
            "max_x": 22,
            "min_y": 0,
            "max_y": 6
        },
        "label_pos": [17, 3]
    },
    {
        "name": "REAR LANAI\nEX-2",
        "number": "EX-2",
        "bounds": {
            "min_x": 12,
            "max_x": 45.333,
            "min_y": 20,
            "max_y": 28.667
        },
        "label_pos": [28, 24]
    },
]

print(f"   Defined {len(rooms)} rooms")

# ============================================================================
# STEP 3: Draw Room Boundary Lines (Diagonal X marks in each room)
# ============================================================================
print("\n3. Drawing room markers...")

lines_created = 0
lines_failed = 0

for room in rooms:
    bounds = room["bounds"]

    # Draw an X in each room to mark it
    # This creates a clear visual indicator

    # Diagonal 1: bottom-left to top-right
    result = send_mcp_request("createDetailLine", {
        "viewId": floor_plan_view_id,
        "startPoint": [bounds["min_x"] + 0.5, bounds["min_y"] + 0.5, 0],
        "endPoint": [bounds["max_x"] - 0.5, bounds["max_y"] - 0.5, 0]
    })

    if result.get("success"):
        lines_created += 1
    else:
        lines_failed += 1
        print(f"   [FAIL] {room['name'].split(chr(10))[0]} line 1: {result.get('error')}")

    # Diagonal 2: top-left to bottom-right
    result = send_mcp_request("createDetailLine", {
        "viewId": floor_plan_view_id,
        "startPoint": [bounds["min_x"] + 0.5, bounds["max_y"] - 0.5, 0],
        "endPoint": [bounds["max_x"] - 0.5, bounds["min_y"] + 0.5, 0]
    })

    if result.get("success"):
        lines_created += 1
    else:
        lines_failed += 1
        print(f"   [FAIL] {room['name'].split(chr(10))[0]} line 2: {result.get('error')}")

print(f"   Created {lines_created} lines, {lines_failed} failed")

# ============================================================================
# STEP 4: Add Room Labels
# ============================================================================
print("\n4. Adding room labels...")

labels_created = 0
labels_failed = 0

for room in rooms:
    # Use single-line name for text note
    room_name = room["name"].replace("\n", " ")
    label_x, label_y = room["label_pos"]

    result = send_mcp_request("createTextNote", {
        "viewId": floor_plan_view_id,
        "position": [label_x, label_y, 0],
        "text": room_name
    })

    if result.get("success"):
        labels_created += 1
        print(f"   [OK] {room_name}")
    else:
        labels_failed += 1
        print(f"   [FAIL] {room_name}: {result.get('error')}")

print(f"\n   Created {labels_created} labels, {labels_failed} failed")

# ============================================================================
# STEP 5: Draw Perimeter Outline
# ============================================================================
print("\n5. Drawing building perimeter outline...")

# Building perimeter points
perimeter = [
    ([0, 0, 0], [45.333, 0, 0]),      # South
    ([45.333, 0, 0], [45.333, 28.667, 0]),  # East
    ([45.333, 28.667, 0], [0, 28.667, 0]),  # North
    ([0, 28.667, 0], [0, 0, 0]),      # West
]

perimeter_created = 0
for start, end in perimeter:
    result = send_mcp_request("createDetailLine", {
        "viewId": floor_plan_view_id,
        "startPoint": start,
        "endPoint": end
    })
    if result.get("success"):
        perimeter_created += 1

print(f"   Created {perimeter_created}/4 perimeter lines")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"   View ID: {floor_plan_view_id}")
print(f"   Room markers (X): {lines_created} lines")
print(f"   Room labels: {labels_created} text notes")
print(f"   Perimeter: {perimeter_created} lines")
print("\nOpen the floor plan view in Revit to see the diagram!")
print("=" * 80)
