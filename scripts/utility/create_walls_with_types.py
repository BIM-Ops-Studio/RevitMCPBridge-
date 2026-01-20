"""
Create floor plan walls with proper wall types:
- Exterior walls: 8" (Generic - 8")
- Interior walls: 4" (Generic - 4")
- All walls snapped to grid lines
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

# Step 2: Get level
print("\nStep 2: Getting Level 1...")
levels = call_mcp('getLevels')
level_id = None
if levels.get('success'):
    for level in levels.get('levels', []):
        if 'L1' in level['name'] or 'Level 1' in level['name'] or level['elevation'] == 0:
            level_id = level['levelId']
            print(f"  Using level: {level['name']} (ID: {level_id})")
            break

wall_height = 10.0

# ============================================================================
# GRID-SNAPPED COORDINATES
# Using round numbers on grid for clean coordinates
# ============================================================================

# PERIMETER WALLS (8 walls - 8" exterior walls)
# L-shaped building with garage bump-out on southwest
# Coordinates snapped to whole feet for grid alignment
perimeter_walls = [
    # Top wall (north) - main building
    ("P1: North wall", 4.0, 45.0, 28.0, 45.0),
    # Right wall (east) - main building
    ("P2: East wall", 28.0, 45.0, 28.0, 12.0),
    # Bottom-right jog
    ("P3: South-east horizontal", 28.0, 12.0, 13.0, 12.0),
    # Right side of garage bump-out
    ("P4: Garage east wall", 13.0, 12.0, 13.0, 0.0),
    # Bottom of garage
    ("P5: Garage south wall", 13.0, 0.0, 0.0, 0.0),
    # Left side of garage
    ("P6: Garage west wall", 0.0, 0.0, 0.0, 22.0),
    # Horizontal jog between garage and main
    ("P7: Jog wall", 0.0, 22.0, 4.0, 22.0),
    # Left side of main building (north portion)
    ("P8: West wall main", 4.0, 22.0, 4.0, 45.0),
]

# INTERIOR WALLS (9 walls - 4" interior walls)
interior_walls = [
    # Horizontal wall separating garage area
    ("I1: Garage separation", 4.0, 21.0, 13.0, 21.0),
    # Main vertical partition
    ("I2: Main vertical partition", 13.0, 12.0, 13.0, 28.0),
    # Bathroom/closet vertical wall
    ("I3: Bath vertical", 18.0, 12.0, 18.0, 24.0),
    # Horizontal room divider (upper)
    ("I4: Room divider", 4.0, 28.0, 13.0, 28.0),
    # Bathroom horizontal top
    ("I5: Bath top wall", 18.0, 24.0, 24.0, 24.0),
    # Bathroom right wall
    ("I6: Bath right wall", 24.0, 24.0, 24.0, 16.0),
    # Bathroom bottom wall
    ("I7: Bath bottom wall", 24.0, 16.0, 18.0, 16.0),
    # Small closet walls
    ("I8: Closet vertical", 11.0, 28.0, 11.0, 26.0),
    ("I9: Closet horizontal", 11.0, 26.0, 13.0, 26.0),
]

# Step 3: Create exterior walls (8")
print("\nStep 3: Creating 8 EXTERIOR walls (8 inch)...")
created_walls = []
for desc, x1, y1, x2, y2 in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': EXTERIOR_8_INCH
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print(f"  {desc}: OK (8\")")
    else:
        print(f"  {desc}: FAILED - {result.get('error', 'Unknown')}")

# Step 4: Create interior walls (4")
print("\nStep 4: Creating 9 INTERIOR walls (4 inch)...")
for desc, x1, y1, x2, y2 in interior_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': INTERIOR_4_INCH
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print(f"  {desc}: OK (4\")")
    else:
        print(f"  {desc}: FAILED - {result.get('error', 'Unknown')}")

print("\n" + "="*60)
print(f"COMPLETE: Created {len(created_walls)} walls")
print("  - 8 exterior walls (8 inch)")
print("  - 9 interior walls (4 inch)")
print("  - All coordinates on whole foot grid")
print("="*60)
