#!/usr/bin/env python3
"""Add more interior walls to complete the 1713 floor plan"""
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

INTERIOR_WALL_TYPE = 441519  # Interior - 4 1/2" Partition
LEVEL_ID = 30  # L1
HEIGHT = 10.0

# Additional interior walls to complete the layout
MORE_WALLS = [
    # Stairway walls
    {"start": (26.67, 0), "end": (26.67, 6), "name": "Stair wall south"},

    # Kitchen peninsula/island wall area
    {"start": (11.33, 17), "end": (21, 17), "name": "Kitchen north wall"},

    # Dining room definition
    {"start": (11.33, 10.67), "end": (11.33, 17), "name": "Dining/Kitchen divider"},

    # Rear lanai separation
    {"start": (0, 21), "end": (11.33, 21), "name": "Lanai separation"},

    # Living room east wall
    {"start": (21, 10.67), "end": (21, 21), "name": "Living room east"},

    # Complete the garage interior
    {"start": (38, 0), "end": (38, 10), "name": "Garage interior east"},
]

def create_more_walls():
    walls_created = []
    errors = []

    print(f"Adding {len(MORE_WALLS)} more interior walls...")

    for i, wall in enumerate(MORE_WALLS):
        start_x, start_y = wall["start"]
        end_x, end_y = wall["end"]

        params = {
            "startPoint": [start_x, start_y, 0.0],
            "endPoint": [end_x, end_y, 0.0],
            "levelId": LEVEL_ID,
            "height": HEIGHT,
            "wallTypeId": INTERIOR_WALL_TYPE
        }

        result = call_mcp("createWallByPoints", params)

        if result.get("success"):
            walls_created.append({
                "index": i,
                "wallId": result.get("wallId"),
                "name": wall["name"]
            })
            print(f"  Wall {i+1}: Created '{wall['name']}' (ID: {result.get('wallId')})")
        else:
            errors.append({
                "index": i,
                "name": wall["name"],
                "error": result.get("error")
            })
            print(f"  Wall {i+1}: ERROR '{wall['name']}' - {result.get('error')}")

    return {
        "success": len(errors) == 0,
        "walls_created": len(walls_created),
        "errors": len(errors),
        "details": walls_created,
        "error_details": errors
    }

if __name__ == "__main__":
    result = create_more_walls()
    print("\n" + "="*50)
    print(f"Result: {result['walls_created']} walls created, {result['errors']} errors")
