"""
Create RBCDC floor plan walls with CORRECT centerline offsets.

KEY LESSON LEARNED:
When using 8" exterior walls with exterior face on grid:
- Wall centerline must be offset 0.333 ft (4 inches = half wall thickness) INWARD from grid
- Grid at X=0 (west edge) → centerline at X=0.333 (offset east)
- Grid at Y=0 (south edge) → centerline at Y=0.333 (offset north)
- Grid at X=28/50 (east edge) → centerline at X-0.333 (offset west, but keep as is for now)
- Grid at Y=45 (north edge) → centerline stays at Y=45 (per user's manual fix)

This script replicates the user's manually-fixed wall layout.
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
        print("  Deleted", delete_result.get('deletedCount', 0), "walls")
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
            print("  Using level:", level['name'])
            break

wall_height = 10.0

# ============================================================================
# WALLS WITH CORRECT CENTERLINE OFFSETS (from user's manual fix)
#
# The 8" exterior walls have centerlines offset 0.333 ft (4") from grid.
# These coordinates were extracted from the user's manually-fixed model.
# ============================================================================

# PERIMETER WALLS (8 walls - 8" exterior walls)
# Coordinates are wall CENTERLINES (not grid lines)
perimeter_walls = [
    # P1: North wall (Y=45.0 - no offset at top)
    ("P1: North wall", 28.333, 45.0, 4.333, 45.0),

    # P2: East wall (X=28.333 - offset 0.333 from grid)
    ("P2: East wall", 28.333, 11.667, 28.333, 45.0),

    # P3: South-east horizontal (Y=11.667 - offset 0.333 from grid 12)
    ("P3: SE horizontal", 13.167, 11.667, 28.333, 11.667),

    # P4: Garage east wall (X=13.333)
    ("P4: Garage E wall", 13.333, 0.333, 13.333, 11.667),

    # P5: Garage south wall (Y=0.333 - offset 0.333 from grid 0)
    ("P5: Garage S wall", 0.333, 0.333, 13.333, 0.333),

    # P6: Garage west wall (X=0.333 - offset 0.333 from grid 0)
    ("P6: Garage W wall", 0.333, 21.667, 0.333, 0.333),

    # P7: Jog wall between garage and main (Y=21.667)
    ("P7: Jog wall", 0.333, 21.667, 4.333, 21.667),

    # P8: West wall main (X=4.333)
    ("P8: West wall main", 4.333, 45.0, 4.333, 21.667),
]

# INTERIOR WALLS (9 walls - 4" interior walls)
# These use centerline positioning
interior_walls = [
    # I1: Garage separation
    ("I1: Garage separation", 4.0, 21.167, 13.167, 21.167),

    # I2: Main vertical partition
    ("I2: Main vertical", 13.167, 11.667, 13.167, 28.0),

    # I3: Bath vertical
    ("I3: Bath vertical", 18.0, 11.667, 18.0, 24.0),

    # I4: Room divider
    ("I4: Room divider", 4.333, 28.0, 13.167, 28.0),

    # I5: Bath top wall
    ("I5: Bath top", 18.0, 24.0, 24.0, 24.0),

    # I6: Bath right wall
    ("I6: Bath right", 24.0, 24.0, 24.0, 16.0),

    # I7: Bath bottom wall
    ("I7: Bath bottom", 24.0, 16.0, 18.0, 16.0),

    # I8: Closet vertical
    ("I8: Closet vertical", 11.0, 28.0, 11.0, 26.0),

    # I9: Closet horizontal
    ("I9: Closet horizontal", 11.0, 26.0, 13.167, 26.0),
]

# Step 3: Create exterior walls (8")
print("\nStep 3: Creating 8 EXTERIOR walls (8 inch, with offset centerlines)...")
created_walls = []
for desc, x1, y1, x2, y2 in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': EXTERIOR_8_INCH,
        'locationLine': 0  # Use centerline since we pre-calculated the offset
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK (8\" wall)")
    else:
        print("  " + desc + ": FAILED -", result.get('error', 'Unknown'))

# Step 4: Create interior walls (4")
print("\nStep 4: Creating 9 INTERIOR walls (4 inch)...")
for desc, x1, y1, x2, y2 in interior_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': INTERIOR_4_INCH,
        'locationLine': 0  # Centerline for interior walls
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK (4\" wall)")
    else:
        print("  " + desc + ": FAILED -", result.get('error', 'Unknown'))

print("\n" + "="*60)
print("COMPLETE: Created", len(created_walls), "walls")
print("  - 8 exterior walls (8\") with centerlines offset from grid")
print("  - 9 interior walls (4\") on centerline")
print("  - Exterior face of 8\" walls should be ON the grid lines")
print("="*60)
