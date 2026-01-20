#!/usr/bin/env python3
"""
Add doors to the RBCDC 1713 floor plan.
Doors placed at logical locations based on room layout.
"""

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


# Door definitions based on floor plan layout
# Coordinates are wall centerline locations where doors go
DOORS = [
    # Front entry - south wall, centered on main portion
    {
        "description": "Front Entry Door",
        "wall_id": 1240862,  # South wall - main building
        "location": [30.0, 0.0, 0.0],  # Center of main south wall
        "width": 3.0  # 3'-0" door
    },
    # Garage to house - through garage separation wall
    {
        "description": "Garage to House Door",
        "wall_id": 1240867,  # Garage separation wall
        "location": [11.333, 14.0, 0.0],  # Middle of garage separation
        "width": 2.667  # 2'-8" door
    },
    # Kitchen to rear lanai
    {
        "description": "Rear Door from Kitchen",
        "wall_id": 1240864,  # North wall
        "location": [16.0, 38.0, 0.0],  # Kitchen area
        "width": 3.0  # 3'-0" door
    },
    # Living room to rear lanai
    {
        "description": "Rear Door from Living Room",
        "wall_id": 1240864,  # North wall
        "location": [35.0, 38.0, 0.0],  # Living room area
        "width": 6.0  # 6'-0" sliding door
    },
    # Bathroom door
    {
        "description": "Bathroom Door",
        "wall_id": 1240872,  # Bathroom partition wall
        "location": [48.0, 21.333, 0.0],  # Bathroom entry
        "width": 2.5  # 2'-6" door
    }
]


def main():
    print("=" * 60)
    print("ADDING DOORS TO RBCDC 1713 FLOOR PLAN")
    print("=" * 60)

    # Get available door types
    print("\nQuerying available door types...")
    result = call_mcp("getDoorTypes")

    door_type_id = None
    if result.get("success"):
        door_types = result.get("doorTypes", [])
        print(f"Found {len(door_types)} door types:")
        for dt in door_types[:5]:  # Show first 5
            print(f"  ID {dt.get('typeId')}: {dt.get('typeName')}")
        if len(door_types) > 5:
            print(f"  ... and {len(door_types) - 5} more")

        # Use first available door type
        if door_types:
            door_type_id = door_types[0].get('typeId')
            print(f"\nUsing door type ID: {door_type_id}")
    else:
        print(f"Error getting door types: {result.get('error')}")
        print("Will try placing doors without specifying type (use default)")

    # Place doors
    print("\n" + "=" * 60)
    print("PLACING DOORS")
    print("=" * 60)

    for door in DOORS:
        print(f"\n{door['description']}:")
        print(f"  Wall ID: {door['wall_id']}")
        print(f"  Location: {door['location']}")
        print(f"  Width: {door['width']}'")

        result = call_mcp("placeDoor", {
            "wallId": door["wall_id"],
            "location": door["location"],
            "doorTypeId": door_type_id
        })

        if result.get("success"):
            print(f"  PLACED: Element ID {result.get('doorId')}")
        else:
            print(f"  FAILED: {result.get('error')}")

    print("\n" + "=" * 60)
    print("DOOR PLACEMENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
