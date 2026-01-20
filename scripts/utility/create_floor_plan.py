#!/usr/bin/env python3
"""Create floor plan elements from spec in Revit"""
import json
import win32file
import pywintypes
import time

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

# Load the floor plan spec
with open('floor_plan_spec.json', 'r') as f:
    spec = json.load(f)

# Get the level ID (use L1 = 30)
level_id = 30

print("Creating walls from floor plan spec...")
print(f"Total walls to create: {len(spec['walls'])}")

created_walls = []
failed_walls = []

for i, wall in enumerate(spec['walls']):
    params = {
        "startPoint": wall['startPoint'],
        "endPoint": wall['endPoint'],
        "levelId": level_id,
        "height": wall.get('height', 10.0)
    }

    result = call('createWall', params)

    if result.get('success'):
        created_walls.append(result['wallId'])
        print(f"  [{i+1}/{len(spec['walls'])}] Wall created: ID {result['wallId']}")
    else:
        failed_walls.append({'index': i, 'error': result.get('error', 'Unknown error')})
        print(f"  [{i+1}/{len(spec['walls'])}] FAILED: {result.get('error', 'Unknown error')}")

    # Small delay between calls
    time.sleep(0.1)

print(f"\n=== SUMMARY ===")
print(f"Created: {len(created_walls)} walls")
print(f"Failed: {len(failed_walls)} walls")

if failed_walls:
    print("\nFailed walls:")
    for fw in failed_walls:
        print(f"  Wall {fw['index']}: {fw['error']}")

# Save created wall IDs for reference
with open('created_wall_ids.json', 'w') as f:
    json.dump({'wallIds': created_walls, 'failed': failed_walls}, f, indent=2)

print("\nWall IDs saved to created_wall_ids.json")
