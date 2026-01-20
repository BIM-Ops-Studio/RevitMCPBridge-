"""
Check all walls in the model to understand current state.
"""

import json
import win32file
import math

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

print("Getting all walls...")
result = call_mcp('getWalls')

if result.get('success'):
    walls = result.get('walls', [])
    print(f"Total walls: {len(walls)}")
    print("="*80)

    # Group by level
    walls_by_level = {}
    for wall in walls:
        level_id = wall.get('levelId')
        if level_id not in walls_by_level:
            walls_by_level[level_id] = []
        walls_by_level[level_id].append(wall)

    # Get level names
    levels = call_mcp('getLevels')
    level_names = {}
    if levels.get('success'):
        for level in levels.get('levels', []):
            level_names[level['levelId']] = f"{level['name']} (elev: {level['elevation']})"
            print(f"Level {level['levelId']}: {level['name']} at {level['elevation']} ft")

    print("\n" + "="*80)
    print("WALLS BY LEVEL:")
    print("="*80)

    for level_id, level_walls in walls_by_level.items():
        level_name = level_names.get(level_id, f"Unknown Level {level_id}")
        print(f"\n{level_name}: {len(level_walls)} walls")
        print("-"*60)

        for wall in level_walls:
            wall_id = wall.get('wallId')
            wall_type_id = wall.get('wallTypeId')
            start = wall.get('start', {})
            end = wall.get('end', {})

            x1, y1 = start.get('x', 0), start.get('y', 0)
            x2, y2 = end.get('x', 0), end.get('y', 0)
            length = math.sqrt((x2-x1)**2 + (y2-y1)**2)

            if wall_type_id == EXTERIOR_8_INCH:
                wall_type = "EXT-8\""
            elif wall_type_id == INTERIOR_4_INCH:
                wall_type = "INT-4\""
            else:
                wall_type = f"Type{wall_type_id}"

            print(f"  ID {wall_id}: {wall_type:8} ({x1:.1f},{y1:.1f}) -> ({x2:.1f},{y2:.1f}) L={length:.1f}ft")

else:
    print("ERROR:", result.get('error'))
