#!/usr/bin/env python3
"""List all available views in the Revit project."""

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

print("Querying views...")
result = send_mcp_request("getViews", {})

if result.get("success"):
    views = result.get("views", [])
    print(f"Found {len(views)} views:\n")

    print(f"{'ID':>10} | {'Type':^20} | Name")
    print("-" * 60)

    for v in views:
        vid = v.get("viewId", "?")
        vtype = v.get("viewType", "Unknown")
        name = v.get("name", "Unnamed")
        print(f"{vid:>10} | {vtype:^20} | {name}")
else:
    print(f"ERROR: {result.get('error')}")

    # Try alternate method
    print("\nTrying getFloorPlans...")
    result = send_mcp_request("getFloorPlans", {})
    if result.get("success"):
        plans = result.get("floorPlans", result.get("views", []))
        print(f"Found {len(plans)} floor plans")
        for p in plans:
            print(f"  {p}")
    else:
        print(f"  ERROR: {result.get('error')}")
