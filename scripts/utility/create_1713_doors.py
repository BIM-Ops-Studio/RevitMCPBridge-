#!/usr/bin/env python3
"""Add doors to walls created from Florida 1713 floor plan"""
import json
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Wall IDs from successful wall creation (interior walls get doors)
WALL_IDS_WITH_DOORS = [
    1240778,  # Interior wall 9 - horizontal partition
    1240781,  # Interior wall 11 - vertical partition
    1240782,  # Interior wall 12 - horizontal partition
    1240785,  # Interior wall 15 - horizontal partition
    1240786,  # Interior wall 16 - vertical partition
]

# Door type IDs
INTERIOR_DOOR_TYPE = 387954  # Door-Passage-Single-Flush 30" x 80"
EXTERIOR_DOOR_TYPE = 464646  # Door-Exterior-Single-Two_Lite 36" x 80"

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

def place_doors():
    doors_created = []
    errors = []

    print(f"Placing {len(WALL_IDS_WITH_DOORS)} doors...")

    for i, wall_id in enumerate(WALL_IDS_WITH_DOORS):
        params = {
            "wallId": wall_id,
            "doorTypeId": INTERIOR_DOOR_TYPE
            # No location = place at wall midpoint
        }

        result = call_mcp("placeDoor", params)

        if result.get("success"):
            doors_created.append({
                "index": i,
                "doorId": result.get("doorId"),
                "wallId": wall_id
            })
            print(f"  Door {i+1}: Created (ID: {result.get('doorId')}) in wall {wall_id}")
        else:
            errors.append({
                "index": i,
                "wallId": wall_id,
                "error": result.get("error")
            })
            print(f"  Door {i+1}: ERROR - {result.get('error')}")

    return {
        "success": len(errors) == 0,
        "doors_created": len(doors_created),
        "errors": len(errors),
        "details": doors_created,
        "error_details": errors
    }

if __name__ == "__main__":
    result = place_doors()
    print("\n" + "="*50)
    print(f"Result: {result['doors_created']} doors created, {result['errors']} errors")
    print(json.dumps(result, indent=2))
