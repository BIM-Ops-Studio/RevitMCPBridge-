#!/usr/bin/env python3
"""Delete all walls from the model."""

import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None
        )
        request = {"method": method, "params": params or {}}
        message = json.dumps(request) + '\n'
        win32file.WriteFile(handle, message.encode('utf-8'))

        response_data = b''
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)
            response_data += chunk
            if b'\n' in chunk or len(chunk) == 0:
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8').strip())
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("Getting all walls...")
    result = call_mcp("getWalls")

    if not result.get("success"):
        print(f"Failed: {result.get('error')}")
        return

    walls = result.get("walls", [])
    print(f"Found {len(walls)} walls")

    if not walls:
        print("No walls to delete")
        return

    # Get element IDs (field is 'wallId' not 'elementId')
    wall_ids = [w.get("wallId") for w in walls if w.get("wallId")]
    print(f"Wall IDs to delete: {wall_ids}")

    if wall_ids:
        print(f"Deleting {len(wall_ids)} walls...")
        result = call_mcp("deleteElements", {"elementIds": wall_ids})
        print(f"Result: {result}")

    # Verify
    print("\nVerifying...")
    result = call_mcp("getWalls")
    if result.get("success"):
        remaining = len(result.get("walls", []))
        print(f"Remaining walls: {remaining}")


if __name__ == "__main__":
    main()
