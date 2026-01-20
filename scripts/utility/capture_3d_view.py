#!/usr/bin/env python3
"""Capture a 3D view screenshot to verify walls"""

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

# Step 1: Get available views
print("Getting views...")
views = send_mcp_request("getViews", {})
if views.get("success"):
    view_list = views.get("views", [])
    print(f"Found {len(view_list)} views")

    # Look for 3D view
    view_3d = None
    for v in view_list:
        if "3D" in v.get("name", "") or v.get("viewType") == "ThreeD":
            view_3d = v
            print(f"  Found 3D view: {v.get('name')} (ID: {v.get('viewId')})")
            break

    # If no 3D view, look for floor plan
    if not view_3d:
        for v in view_list:
            if "plan" in v.get("name", "").lower() or v.get("viewType") == "FloorPlan":
                view_3d = v
                print(f"  Using floor plan view: {v.get('name')} (ID: {v.get('viewId')})")
                break

    if view_3d:
        # Step 2: Export view to image
        print(f"\nExporting view to image...")
        result = send_mcp_request("exportViewToImage", {
            "viewId": view_3d.get("viewId"),
            "filePath": "D:/RevitMCPBridge2026/first_floor_walls.png",
            "pixelSize": 1920
        })
        if result.get("success"):
            print(f"  Screenshot saved to: {result.get('filePath')}")
        else:
            print(f"  Failed: {result.get('error')}")
    else:
        print("No suitable view found")
else:
    print(f"Failed to get views: {views.get('error')}")
