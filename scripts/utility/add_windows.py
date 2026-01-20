#!/usr/bin/env python3
"""
Add windows to the RBCDC 1713 floor plan.
Windows placed for natural light based on room layout.
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


# Window definitions based on floor plan layout
# Building dimensions: 52.333' wide x 38' deep
# Garage: X=0 to 11.333, Y=0 to 21.333

WINDOWS = [
    # South wall windows (front of building)
    {
        "description": "South Wall - Foyer Window",
        "wall_id": 1240862,  # South wall - main building
        "location": [20.0, 0.0, 3.0],  # Foyer area, 3' above floor
    },
    {
        "description": "South Wall - Living Room Window 1",
        "wall_id": 1240862,
        "location": [38.0, 0.0, 3.0],  # Living room
    },
    {
        "description": "South Wall - Living Room Window 2",
        "wall_id": 1240862,
        "location": [46.0, 0.0, 3.0],  # Living room
    },

    # East wall windows
    {
        "description": "East Wall - Living Room Window",
        "wall_id": 1240863,  # East wall
        "location": [52.333, 10.0, 3.0],  # Living room area
    },
    {
        "description": "East Wall - Bedroom Window",
        "wall_id": 1240863,
        "location": [52.333, 30.0, 3.0],  # Bedroom area
    },

    # North wall windows (rear of building)
    {
        "description": "North Wall - Kitchen Window",
        "wall_id": 1240864,  # North wall
        "location": [10.0, 38.0, 4.0],  # Above counter height
    },
    {
        "description": "North Wall - Bedroom Window 1",
        "wall_id": 1240864,
        "location": [30.0, 38.0, 3.0],  # Bedroom area
    },
    {
        "description": "North Wall - Bedroom Window 2",
        "wall_id": 1240864,
        "location": [50.0, 38.0, 3.0],  # Bedroom area
    },

    # West wall windows
    {
        "description": "West Wall - Kitchen Window",
        "wall_id": 1240865,  # West wall north portion
        "location": [0.0, 28.0, 4.0],  # Kitchen area, above counter
    },

    # Garage window
    {
        "description": "Garage Window",
        "wall_id": 1240866,  # West wall garage portion
        "location": [0.0, 10.0, 4.0],  # Mid-garage
    }
]


def main():
    print("=" * 60)
    print("ADDING WINDOWS TO RBCDC 1713 FLOOR PLAN")
    print("=" * 60)

    # Get available window types
    print("\nQuerying available window types...")
    result = call_mcp("getWindowTypes")

    window_type_id = None
    if result.get("success"):
        window_types = result.get("windowTypes", [])
        print(f"Found {len(window_types)} window types:")
        for wt in window_types[:5]:  # Show first 5
            print(f"  ID {wt.get('typeId')}: {wt.get('typeName')}")
        if len(window_types) > 5:
            print(f"  ... and {len(window_types) - 5} more")

        # Use first available window type
        if window_types:
            window_type_id = window_types[0].get('typeId')
            print(f"\nUsing window type ID: {window_type_id}")
    else:
        print(f"Error getting window types: {result.get('error')}")
        print("Will try placing windows without specifying type (use default)")

    # Place windows
    print("\n" + "=" * 60)
    print("PLACING WINDOWS")
    print("=" * 60)

    placed_count = 0
    failed_count = 0

    for window in WINDOWS:
        print(f"\n{window['description']}:")
        print(f"  Wall ID: {window['wall_id']}")
        print(f"  Location: {window['location']}")

        result = call_mcp("placeWindow", {
            "wallId": window["wall_id"],
            "location": window["location"],
            "windowTypeId": window_type_id
        })

        if result.get("success"):
            print(f"  PLACED: Element ID {result.get('windowId')}")
            placed_count += 1
        else:
            print(f"  FAILED: {result.get('error')}")
            failed_count += 1

    print("\n" + "=" * 60)
    print("WINDOW PLACEMENT SUMMARY")
    print("=" * 60)
    print(f"Placed: {placed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total attempted: {len(WINDOWS)}")


if __name__ == "__main__":
    main()
