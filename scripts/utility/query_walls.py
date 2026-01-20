#!/usr/bin/env python3
"""Query current walls in Revit model"""
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

# Query current walls to see what was created
result = call_mcp('getWalls')
if result.get("success"):
    walls = result.get("walls", [])
    print(f"Total walls: {len(walls)}")
    print()
    for w in walls:
        wid = w.get("wallId")
        wtype = "EXT" if "Exterior" in w.get("wallType", "") else "INT"
        start = w.get("startPoint", {})
        end = w.get("endPoint", {})
        sx, sy = start.get("x", 0), start.get("y", 0)
        ex, ey = end.get("x", 0), end.get("y", 0)
        length = w.get("length", 0)
        print(f"  ID {wid}: [{wtype}] ({sx:.1f}, {sy:.1f}) -> ({ex:.1f}, {ey:.1f}) L={length:.1f}'")
else:
    print(f"Error: {result.get('error')}")
