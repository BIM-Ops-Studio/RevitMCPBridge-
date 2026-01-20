#!/usr/bin/env python3
"""
Query available wall types in Revit to find appropriate types for:
- W1: Exterior 8" CMU + insulation (~11" total)
- W2: Interior Load Bearing 2x4 wood (~5" total)
- W3: Interior Non-Bearing 3-5/8" metal stud (~4-5" total)
"""

import json
import sys

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

        # Read response - keep reading until we get complete JSON
        response_data = b""
        max_attempts = 100
        for _ in range(max_attempts):
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            try:
                decoded = response_data.decode('utf-8').strip()
                # Try to parse as JSON to check if complete
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                # Not complete yet, continue reading
                import time
                time.sleep(0.01)
                continue
            except UnicodeDecodeError:
                continue

        win32file.CloseHandle(handle)
        return {"success": False, "error": f"Response incomplete after {max_attempts} reads. Got {len(response_data)} bytes"}
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running"}
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("QUERYING WALL TYPES IN REVIT")
print("=" * 80)

# Test connection
print("\n1. Testing connection...")
result = send_mcp_request("getLevels", {})
if not result.get("success"):
    print(f"   ERROR: {result.get('error')}")
    sys.exit(1)
print("   Connected!")

# Query wall types
print("\n2. Querying wall types...")
result = send_mcp_request("getWallTypes", {})

if result.get("success"):
    wall_types = result.get("wallTypes", [])
    print(f"\n   Found {len(wall_types)} wall types:\n")

    # Sort by width for easier reading
    wall_types_sorted = sorted(wall_types, key=lambda x: x.get("width", 0))

    print("   {:>8} | {:>10} | {}".format("ID", "Width (ft)", "Name"))
    print("   " + "-" * 60)

    for wt in wall_types_sorted:
        wt_id = wt.get("wallTypeId", "N/A")
        width = wt.get("width", 0)
        name = wt.get("name", "Unknown")
        # Convert width to inches for readability
        width_inches = width * 12
        print(f"   {wt_id:>8} | {width_inches:>7.2f}\" | {name}")

    # Look for candidates for W1, W2, W3
    print("\n" + "=" * 80)
    print("WALL TYPE CANDIDATES FOR A-100 SPECIFICATIONS:")
    print("=" * 80)

    print("\nW1 - Exterior (target: ~11\" = 0.917 ft):")
    for wt in wall_types_sorted:
        width = wt.get("width", 0)
        width_inches = width * 12
        if 8 < width_inches < 14:  # 8" to 14" range for exterior
            print(f"   ID {wt.get('wallTypeId')}: {wt.get('name')} ({width_inches:.2f}\")")

    print("\nW2 - Interior Load Bearing (target: ~5\" = 0.417 ft):")
    for wt in wall_types_sorted:
        width = wt.get("width", 0)
        width_inches = width * 12
        if 4 < width_inches < 7:  # 4" to 7" range
            print(f"   ID {wt.get('wallTypeId')}: {wt.get('name')} ({width_inches:.2f}\")")

    print("\nW3 - Interior Non-Bearing (target: ~4\" = 0.333 ft):")
    for wt in wall_types_sorted:
        width = wt.get("width", 0)
        width_inches = width * 12
        if 3 < width_inches <= 5:  # 3" to 5" range
            print(f"   ID {wt.get('wallTypeId')}: {wt.get('name')} ({width_inches:.2f}\")")

    print("\n" + "=" * 80)
    print("All available widths (in inches):")
    widths = set()
    for wt in wall_types_sorted:
        width_inches = wt.get("width", 0) * 12
        widths.add(round(width_inches, 2))
    print("   " + ", ".join(f"{w}\"" for w in sorted(widths)))

else:
    print(f"   ERROR: {result.get('error')}")

print("\n" + "=" * 80)
