"""
Replicate the user's manually-drawn floor plan.
Based on analysis of 17 walls in the Revit model.

The building is L-shaped with a garage bump-out on the southwest.
"""

import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    """Call Revit MCP bridge."""
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


# Step 1: Delete all existing walls
print("Step 1: Deleting all existing walls...")
walls_result = call_mcp('getWalls')
if walls_result.get('success') and walls_result.get('walls'):
    wall_ids = [w.get('wallId') for w in walls_result['walls'] if w.get('wallId')]
    if wall_ids:
        delete_result = call_mcp('deleteElements', {'elementIds': wall_ids})
        print(f"  Deleted {delete_result.get('deletedCount', 0)} walls")
else:
    print("  No walls to delete")

# Step 2: Get level and wall type
print("\nStep 2: Getting Level 1 and wall type...")
levels = call_mcp('getLevels')
level_id = None
if levels.get('success'):
    for level in levels.get('levels', []):
        if 'L1' in level['name'] or 'Level 1' in level['name'] or level['elevation'] == 0:
            level_id = level['levelId']
            print(f"  Using level: {level['name']} (ID: {level_id})")
            break

wall_types = call_mcp('getWallTypes')
wall_type_id = None
if wall_types.get('success'):
    for wt in wall_types.get('wallTypes', []):
        if 'Generic' in wt['name'] or 'Basic' in wt['name']:
            wall_type_id = wt['wallTypeId']
            print(f"  Using wall type: {wt['name']}")
            break
    if not wall_type_id and wall_types.get('wallTypes'):
        wall_type_id = wall_types['wallTypes'][0]['wallTypeId']

wall_height = 10.0

# ============================================================================
# WALLS FROM USER'S MANUAL DRAWING
# ============================================================================
# Extracted from getWalls output - exact coordinates from user's drawing

# PERIMETER WALLS (8 walls forming L-shape, counter-clockwise from top-left)
perimeter_walls = [
    # Top wall (north) - main building
    ("P1: North wall", 4.333, 45.0, 28.333, 45.0),
    # Right wall (east) - main building
    ("P2: East wall", 28.333, 45.0, 28.333, 11.667),
    # Bottom-right jog
    ("P3: South-east horizontal", 28.333, 11.667, 13.167, 11.667),
    # Right side of garage bump-out
    ("P4: Garage east wall", 13.333, 11.667, 13.333, 0.333),
    # Bottom of garage
    ("P5: Garage south wall", 13.333, 0.333, 0.333, 0.333),
    # Left side of garage
    ("P6: Garage west wall", 0.333, 0.333, 0.333, 21.667),
    # Horizontal jog between garage and main
    ("P7: Jog wall", 0.333, 21.667, 4.333, 21.667),
    # Left side of main building (north portion)
    ("P8: West wall main", 4.333, 21.667, 4.333, 45.0),
]

# INTERIOR WALLS (9 walls for room divisions)
interior_walls = [
    # Horizontal wall separating garage area
    ("I1: Garage separation", 4.0, 21.167, 13.167, 21.167),
    # Main vertical partition
    ("I2: Main vertical partition", 13.167, 11.667, 13.167, 27.5),
    # Bathroom/closet vertical wall
    ("I3: Bath vertical", 17.917, 11.667, 17.917, 23.5),
    # Horizontal room divider (upper)
    ("I4: Room divider", 4.333, 27.5, 13.167, 27.5),
    # Bathroom horizontal top
    ("I5: Bath top wall", 17.917, 23.5, 23.833, 23.5),
    # Bathroom right wall
    ("I6: Bath right wall", 23.833, 23.5, 23.833, 16.167),
    # Bathroom bottom wall
    ("I7: Bath bottom wall", 23.833, 16.167, 17.917, 16.167),
    # Small closet walls
    ("I8: Closet vertical", 10.833, 27.5, 10.833, 25.917),
    ("I9: Closet horizontal", 10.833, 25.917, 13.167, 25.917),
]

# Step 3: Create all perimeter walls
print("\nStep 3: Creating 8 perimeter walls...")
created_walls = []
for desc, x1, y1, x2, y2 in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': wall_type_id
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print(f"  {desc}: OK")
    else:
        print(f"  {desc}: FAILED - {result.get('error', 'Unknown')}")

# Step 4: Create all interior walls
print("\nStep 4: Creating 9 interior walls...")
for desc, x1, y1, x2, y2 in interior_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': wall_type_id
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print(f"  {desc}: OK")
    else:
        print(f"  {desc}: FAILED - {result.get('error', 'Unknown')}")

print("\n" + "="*60)
print(f"COMPLETE: Created {len(created_walls)} walls")
print("="*60)
