#!/usr/bin/env python3
"""Debug: Check what getWalls returns."""

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
    print("Getting walls with full debug output...")
    result = call_mcp("getWalls")

    print(f"\nFull response:")
    print(json.dumps(result, indent=2)[:2000])

    if result.get("success"):
        walls = result.get("walls", [])
        print(f"\nNumber of walls: {len(walls)}")

        if walls:
            print("\nFirst wall details:")
            print(json.dumps(walls[0], indent=2))

            print("\nAll wall keys available:")
            for key in walls[0].keys():
                print(f"  - {key}: {walls[0][key]}")


if __name__ == "__main__":
    main()
