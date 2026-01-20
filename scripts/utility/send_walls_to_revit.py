#!/usr/bin/env python3
"""Send cleaned structural walls to Revit via MCP bridge."""

import json
import struct
import time

PIPE_PATH = r"\\.\pipe\RevitMCPBridge2026"

def send_mcp_request(method: str, params: dict = None) -> dict:
    """Send a request to the Revit MCP bridge via named pipe."""
    import win32file
    import win32pipe
    import pywintypes

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    request_json = json.dumps(request)
    request_bytes = request_json.encode('utf-8')

    try:
        # Open pipe
        handle = win32file.CreateFile(
            PIPE_PATH,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        # Send length prefix + message
        length_bytes = struct.pack('<I', len(request_bytes))
        win32file.WriteFile(handle, length_bytes + request_bytes)

        # Read response length
        _, length_data = win32file.ReadFile(handle, 4)
        response_length = struct.unpack('<I', length_data)[0]

        # Read response
        _, response_data = win32file.ReadFile(handle, response_length)
        response = json.loads(response_data.decode('utf-8'))

        win32file.CloseHandle(handle)
        return response

    except pywintypes.error as e:
        return {"error": f"Pipe error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    # Load walls
    with open('D:/RevitMCPBridge2026/cleaned_walls.json') as f:
        data = json.load(f)

    walls = data['walls']
    print(f"Loaded {len(walls)} walls to create")

    # Test connection
    print("\nTesting connection...")
    response = send_mcp_request("getLevels")
    if "error" in response:
        print(f"Connection error: {response['error']}")
        return

    result = response.get("result", {})
    if not result.get("success"):
        print(f"getLevels failed: {result}")
        return

    levels = result.get("levels", [])
    print(f"Connected! Found {len(levels)} levels:")
    for level in levels:
        print(f"  {level['name']}: {level['elevation']}' (ID: {level['id']})")

    # Use first level
    level_id = levels[0]['id'] if levels else 0
    print(f"\nUsing level ID: {level_id}")

    # Create walls
    print(f"\nCreating {len(walls)} walls...")
    success_count = 0
    fail_count = 0

    for i, wall in enumerate(walls):
        # Update level ID
        wall['levelId'] = level_id

        response = send_mcp_request("createWall", wall)
        result = response.get("result", {})

        if result.get("success"):
            success_count += 1
            wall_id = result.get("wallId", "unknown")
            print(f"  Wall {i+1}: Created (ID: {wall_id})")
        else:
            fail_count += 1
            error = result.get("error", response.get("error", "Unknown error"))
            print(f"  Wall {i+1}: FAILED - {error}")

        # Small delay to avoid overwhelming Revit
        time.sleep(0.1)

    print(f"\nDone! Created {success_count} walls, {fail_count} failed")


if __name__ == "__main__":
    main()
