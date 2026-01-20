"""
Create floor plan walls with CORRECT exterior face positioning.

The key insight: 
- locationLine=2 (FinishFaceExterior) puts the exterior face on the wall line
- But "exterior" is determined by the wall's DIRECTION
- Wall direction goes from start to end, and exterior is to the RIGHT of that direction

So for a wall to have its exterior face on the correct grid:
- South wall (exterior facing SOUTH): draw WEST to EAST, exterior is on SOUTH (right side)
- North wall (exterior facing NORTH): draw EAST to WEST, exterior is on NORTH (right side)  
- East wall (exterior facing EAST): draw SOUTH to NORTH, exterior is on EAST (right side)
- West wall (exterior facing WEST): draw NORTH to SOUTH, exterior is on WEST (right side)

Wall Location Line values:
- 0 = WallCenterline
- 1 = CoreCenterline
- 2 = FinishFaceExterior (exterior = RIGHT of wall direction)
- 3 = FinishFaceInterior (interior = LEFT of wall direction)
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
# PERIMETER WALLS with CORRECT direction for exterior face positioning
# 
# Grid layout:
#   Grid 1: X=0 (west edge)
#   Grid 3: X=13 (garage/main division)
#   Grid 5: X=28 (east edge)
#   Grid A: Y=0 (south edge)
#   Grid B: Y=22 (garage top / main bottom)
#   Grid D: Y=45 (north edge)
#
# For exterior face on grid using locationLine=2:
# - Draw wall so the OUTSIDE is to the RIGHT of the direction
# ============================================================================

perimeter_walls = [
    # P1: North wall at Y=45 - exterior faces NORTH (up)
    # Draw EAST to WEST so exterior (right) is NORTH
    ("P1: North wall (ext face N)", 28.0, 45.0, 4.0, 45.0, 2),
    
    # P2: East wall at X=28 - exterior faces EAST (right)
    # Draw SOUTH to NORTH so exterior (right) is EAST
    ("P2: East wall (ext face E)", 28.0, 12.0, 28.0, 45.0, 2),
    
    # P3: South-east horizontal at Y=12 - exterior faces SOUTH
    # Draw WEST to EAST so exterior (right) is SOUTH
    ("P3: SE wall (ext face S)", 13.0, 12.0, 28.0, 12.0, 2),
    
    # P4: Garage east wall at X=13 - exterior faces EAST (into main building)
    # Draw SOUTH to NORTH so exterior (right) is EAST
    ("P4: Garage E wall (ext face E)", 13.0, 0.0, 13.0, 12.0, 2),
    
    # P5: Garage south wall at Y=0 (Grid A) - exterior faces SOUTH
    # Draw WEST to EAST so exterior (right) is SOUTH
    ("P5: Garage S wall (ext face S)", 0.0, 0.0, 13.0, 0.0, 2),
    
    # P6: Garage west wall at X=0 - exterior faces WEST
    # Draw NORTH to SOUTH so exterior (right) is WEST
    ("P6: Garage W wall (ext face W)", 0.0, 22.0, 0.0, 0.0, 2),
    
    # P7: Jog wall at Y=22 (Grid B) - exterior faces SOUTH
    # Draw WEST to EAST so exterior (right) is SOUTH
    ("P7: Jog wall (ext face S)", 0.0, 22.0, 4.0, 22.0, 2),
    
    # P8: West wall main at X=4 - exterior faces WEST
    # Draw NORTH to SOUTH so exterior (right) is WEST
    ("P8: West wall main (ext face W)", 4.0, 45.0, 4.0, 22.0, 2),
]

# Interior walls - use centerline (0)
interior_walls = [
    ("I1: Garage separation", 4.0, 21.0, 13.0, 21.0, 0),
    ("I2: Main vertical partition", 13.0, 12.0, 13.0, 28.0, 0),
    ("I3: Bath vertical", 18.0, 12.0, 18.0, 24.0, 0),
    ("I4: Room divider", 4.0, 28.0, 13.0, 28.0, 0),
    ("I5: Bath top wall", 18.0, 24.0, 24.0, 24.0, 0),
    ("I6: Bath right wall", 24.0, 24.0, 24.0, 16.0, 0),
    ("I7: Bath bottom wall", 24.0, 16.0, 18.0, 16.0, 0),
    ("I8: Closet vertical", 11.0, 28.0, 11.0, 26.0, 0),
    ("I9: Closet horizontal", 11.0, 26.0, 13.0, 26.0, 0),
]

# Step 3: Create exterior walls
print("\nStep 3: Creating 8 EXTERIOR walls (8 inch, exterior face on grid)...")
created_walls = []
for desc, x1, y1, x2, y2, loc_line in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': EXTERIOR_8_INCH,
        'locationLine': loc_line
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK")
    else:
        print("  " + desc + ": FAILED -", result.get('error', 'Unknown'))

# Step 4: Create interior walls
print("\nStep 4: Creating 9 INTERIOR walls (4 inch, centerline)...")
for desc, x1, y1, x2, y2, loc_line in interior_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': INTERIOR_4_INCH,
        'locationLine': loc_line
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK")
    else:
        print("  " + desc + ": FAILED -", result.get('error', 'Unknown'))

print("\n" + "="*60)
print("COMPLETE: Created", len(created_walls), "walls")
print("  - Exterior walls drawn with correct direction")
print("  - Exterior face should now be on grid lines")
print("="*60)
