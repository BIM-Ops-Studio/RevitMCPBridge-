#!/usr/bin/env python3
"""Delete the incorrectly placed walls"""
import json
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Wall IDs from the incorrect wall creation
BAD_WALL_IDS = [
    1240768, 1240769, 1240770, 1240771, 1240772, 1240773, 1240774,
    1240777, 1240778, 1240781, 1240782, 1240783, 1240784, 1240785, 1240786
]

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

if __name__ == "__main__":
    print(f"Deleting {len(BAD_WALL_IDS)} incorrectly placed walls...")

    result = call_mcp("deleteElements", {"elementIds": BAD_WALL_IDS})

    if result.get("success"):
        print(f"Successfully deleted {result.get('deletedCount', 0)} elements")
    else:
        print(f"Error: {result.get('error')}")

    print(json.dumps(result, indent=2))
