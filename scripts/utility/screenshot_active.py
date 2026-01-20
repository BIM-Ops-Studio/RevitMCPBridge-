#!/usr/bin/env python3
"""Take screenshot of active Revit view"""

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

# Try to get active view info first
print("Getting active view info...")
result = send_mcp_request("getActiveView", {})
print(f"Active view result: {result}")

# Export active view to image
print("\nExporting active view to image...")
result = send_mcp_request("exportViewToImage", {
    "filePath": "D:/RevitMCPBridge2026/first_floor_walls.png",
    "pixelSize": 1920
})

if result.get("success"):
    print(f"Screenshot saved to: {result.get('filePath')}")
else:
    print(f"Failed: {result.get('error')}")

    # Try alternative - captureActiveView
    print("\nTrying captureActiveView...")
    result = send_mcp_request("captureActiveView", {
        "filePath": "D:/RevitMCPBridge2026/first_floor_walls.png"
    })
    print(f"Result: {result}")
