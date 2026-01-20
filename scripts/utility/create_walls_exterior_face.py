"""
Create floor plan walls with EXTERIOR FACE on grid line.

Wall Location Line options in Revit:
- WallLocationLine.WallCenterline = 0
- WallLocationLine.CoreCenterline = 1
- WallLocationLine.FinishFaceExterior = 2
- WallLocationLine.FinishFaceInterior = 3
- WallLocationLine.CoreExterior = 4
- WallLocationLine.CoreInterior = 5

We need to use FinishFaceExterior (2) so the exterior face snaps to grid.
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
# GRID-SNAPPED COORDINATES - EXTERIOR FACE ON GRID
# For exterior walls: the OUTSIDE face should be on the grid line
# Since walls are drawn from their location line, we need to account for this
# ============================================================================

# Wall thickness in feet
EXT_THICKNESS = 8.0 / 12.0  # 8 inches = 0.667 ft
INT_THICKNESS = 4.0 / 12.0  # 4 inches = 0.333 ft

# PERIMETER WALLS (8 walls - 8" exterior walls)
# Grid coordinates define the EXTERIOR FACE of the building
# L-shaped building: garage bump-out on southwest
perimeter_walls = [
    # Top wall (north) - exterior face at Y=45
    ("P1: North wall", 4.0, 45.0, 28.0, 45.0),
    # Right wall (east) - exterior face at X=28
    ("P2: East wall", 28.0, 45.0, 28.0, 12.0),
    # Bottom-right jog - exterior face at Y=12
    ("P3: South-east horizontal", 28.0, 12.0, 13.0, 12.0),
    # Right side of garage bump-out - exterior face at X=13
    ("P4: Garage east wall", 13.0, 12.0, 13.0, 0.0),
    # Bottom of garage - exterior face at Y=0
    ("P5: Garage south wall", 13.0, 0.0, 0.0, 0.0),
    # Left side of garage - exterior face at X=0
    ("P6: Garage west wall", 0.0, 0.0, 0.0, 22.0),
    # Horizontal jog between garage and main - exterior face at Y=22
    ("P7: Jog wall", 0.0, 22.0, 4.0, 22.0),
    # Left side of main building - exterior face at X=4
    ("P8: West wall main", 4.0, 22.0, 4.0, 45.0),
]

# INTERIOR WALLS (9 walls - 4" interior walls)
# Interior walls use centerline positioning
interior_walls = [
    ("I1: Garage separation", 4.0, 21.0, 13.0, 21.0),
    ("I2: Main vertical partition", 13.0, 12.0, 13.0, 28.0),
    ("I3: Bath vertical", 18.0, 12.0, 18.0, 24.0),
    ("I4: Room divider", 4.0, 28.0, 13.0, 28.0),
    ("I5: Bath top wall", 18.0, 24.0, 24.0, 24.0),
    ("I6: Bath right wall", 24.0, 24.0, 24.0, 16.0),
    ("I7: Bath bottom wall", 24.0, 16.0, 18.0, 16.0),
    ("I8: Closet vertical", 11.0, 28.0, 11.0, 26.0),
    ("I9: Closet horizontal", 11.0, 26.0, 13.0, 26.0),
]

# Step 3: Create exterior walls (8") with exterior face on grid
# Using locationLine parameter: 2 = FinishFaceExterior
print("\nStep 3: Creating 8 EXTERIOR walls (8 inch, exterior face on grid)...")
created_walls = []
for desc, x1, y1, x2, y2 in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': EXTERIOR_8_INCH,
        'locationLine': 2  # FinishFaceExterior - exterior face on the line
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK (8\", ext face on grid)")
    else:
        error = result.get('error', 'Unknown')
        print("  " + desc + ": FAILED -", error)

# Step 4: Create interior walls (4") - centerline is fine for interior
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
        print("  " + desc + ": OK (4\")")
    else:
        error = result.get('error', 'Unknown')
        print("  " + desc + ": FAILED -", error)

print("\n" + "="*60)
print("COMPLETE: Created", len(created_walls), "walls")
print("  - 8 exterior walls (8\") with EXTERIOR FACE on grid")
print("  - 9 interior walls (4\") with centerline positioning")
print("="*60)
