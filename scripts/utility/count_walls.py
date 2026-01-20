#!/usr/bin/env python3
"""Count walls in the model"""

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

        # Read all chunks until we have the complete response
        response_data = b""
        while True:
            result, chunk = win32file.ReadFile(handle, 64 * 1024)  # 64KB chunks
            response_data += chunk
            # Check if we have a complete JSON response (ends with newline or valid JSON)
            try:
                decoded = response_data.decode('utf-8').strip()
                if decoded.endswith('}') or decoded.endswith(']'):
                    json.loads(decoded)  # Validate it's complete JSON
                    break
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not complete yet, keep reading
                pass
            if len(chunk) < 64 * 1024:
                # Last chunk was smaller than buffer - we're done
                break

        win32file.CloseHandle(handle)
        return json.loads(response_data.decode('utf-8'))
    except Exception as e:
        return {"success": False, "error": str(e)}

print("Getting walls...")
result = send_mcp_request("getWalls", {})
if result.get("success"):
    walls = result.get("walls", [])
    print(f"\nTotal walls: {len(walls)}")
    for w in walls:
        length = w.get("length", 0)
        height = w.get("height", 0)
        start = w.get("startPoint", {})
        end = w.get("endPoint", {})
        print(f"  Wall {w.get('wallId')}: Type={w.get('wallType')}, Length={length:.2f}', Height={height:.2f}'")
        print(f"    Start: ({start.get('x', 0):.2f}, {start.get('y', 0):.2f}) -> End: ({end.get('x', 0):.2f}, {end.get('y', 0):.2f})")
else:
    print(f"Failed: {result.get('error')}")
