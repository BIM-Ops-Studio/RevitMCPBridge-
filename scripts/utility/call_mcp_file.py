#!/usr/bin/env python3
"""MCP call using params from file"""
import json
import sys
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call(method, params=None):
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
    except pywintypes.error as e:
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: call_mcp_file.py <method> <params_file.json>"}))
        sys.exit(1)

    method = sys.argv[1]
    with open(sys.argv[2], 'r') as f:
        params = json.load(f)

    result = call(method, params)
    print(json.dumps(result, indent=2))
