"""
Get all walls on Level 2 to identify interior walls for deletion.
"""

import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    handle = win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )
    request = {'method': method, 'params': params or {}}
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

# Wall type IDs
EXTERIOR_8_INCH = 441451  # Generic - 8"
INTERIOR_4_INCH = 441518  # Generic - 4"

print("Getting walls on Level 2...")
result = call_mcp('getWalls')

if result.get('success'):
    walls = result.get('walls', [])
    print(f"\nTotal walls in model: {len(walls)}")

    # Find Level 2 ID
    levels = call_mcp('getLevels')
    level_2_id = None
    if levels.get('success'):
        for level in levels.get('levels', []):
            if 'L2' in level['name'] or 'Level 2' in level['name']:
                level_2_id = level['levelId']
                print(f"Level 2 ID: {level_2_id}")
                break

    # Filter walls on Level 2
    level_2_walls = []
    for wall in walls:
        if wall.get('levelId') == level_2_id:
            level_2_walls.append(wall)

    print(f"\nWalls on Level 2: {len(level_2_walls)}")
    print("="*80)

    exterior_walls = []
    interior_walls = []

    for wall in level_2_walls:
        wall_id = wall.get('wallId')
        wall_type_id = wall.get('wallTypeId')
        start = wall.get('start', {})
        end = wall.get('end', {})

        x1, y1 = start.get('x', 0), start.get('y', 0)
        x2, y2 = end.get('x', 0), end.get('y', 0)

        # Calculate length
        import math
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)

        wall_info = {
            'id': wall_id,
            'typeId': wall_type_id,
            'start': (x1, y1),
            'end': (x2, y2),
            'length': length
        }

        if wall_type_id == EXTERIOR_8_INCH:
            exterior_walls.append(wall_info)
            wall_type = "EXTERIOR (8\")"
        elif wall_type_id == INTERIOR_4_INCH:
            interior_walls.append(wall_info)
            wall_type = "INTERIOR (4\")"
        else:
            interior_walls.append(wall_info)  # Assume unknown types are interior
            wall_type = f"UNKNOWN ({wall_type_id})"

        print(f"Wall ID {wall_id}: {wall_type}")
        print(f"  Start: ({x1:.2f}, {y1:.2f})")
        print(f"  End:   ({x2:.2f}, {y2:.2f})")
        print(f"  Length: {length:.2f} ft")
        print()

    print("="*80)
    print(f"SUMMARY:")
    print(f"  Exterior walls (8\"): {len(exterior_walls)}")
    print(f"  Interior walls (4\"): {len(interior_walls)}")
    print()

    # Output interior wall IDs for deletion
    if interior_walls:
        print("INTERIOR WALL IDs TO DELETE:")
        interior_ids = [w['id'] for w in interior_walls]
        print(interior_ids)
else:
    print("ERROR:", result.get('error'))
