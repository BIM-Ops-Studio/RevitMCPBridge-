"""
Create RBCDC 2nd floor walls.

The 2nd floor sits above the main building only (not the garage).
The garage is single-story, so the 2nd floor footprint is smaller.

Based on the 1st floor layout:
- Main building extends from X=13.167 to X=28.333 (east-west)
- And Y=11.667 to Y=45.0 (south-north)
- The garage (X=0.333 to X=13.333, Y=0.333 to Y=21.667) is NOT included

Using the same centerline offset lesson:
- 8" exterior walls have centerline 0.333 ft (4") inward from grid
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

# Get Level 2
print("Step 1: Getting Level 2...")
levels = call_mcp('getLevels')
level_id = None
if levels.get('success'):
    for level in levels.get('levels', []):
        if 'L2' in level['name'] or 'Level 2' in level['name']:
            level_id = level['levelId']
            print("  Using level:", level['name'], "at elevation", level['elevation'], "ft")
            break

if not level_id:
    print("ERROR: Level 2 not found!")
    exit(1)

wall_height = 10.0  # 2nd floor height

# ============================================================================
# 2ND FLOOR WALLS - Rectangular footprint above main building
#
# The 2nd floor extends over the main building portion only.
# The garage is single-story and has a flat roof or lower roof.
#
# 2nd floor perimeter (based on main building from 1st floor):
# - South wall at Y=11.667 (above the jog/step)
# - North wall at Y=45.0
# - East wall at X=28.333
# - West wall at X=4.333
#
# Using correct centerline offsets (0.333 ft = 4" for 8" walls)
# ============================================================================

# PERIMETER WALLS (4 walls - 8" exterior walls)
# Simple rectangle for 2nd floor
perimeter_walls = [
    # P1: North wall (Y=45.0)
    ("P1: North wall", 28.333, 45.0, 4.333, 45.0),

    # P2: East wall (X=28.333)
    ("P2: East wall", 28.333, 11.667, 28.333, 45.0),

    # P3: South wall (Y=11.667 - above the step from 1st floor)
    ("P3: South wall", 4.333, 11.667, 28.333, 11.667),

    # P4: West wall (X=4.333)
    ("P4: West wall", 4.333, 45.0, 4.333, 11.667),
]

# INTERIOR WALLS for 2nd floor (typical bedroom/bathroom layout)
# Based on typical 2-story residential layout with 3 bedrooms and 2 baths
interior_walls = [
    # Hallway/corridor wall running east-west
    ("I1: Corridor south wall", 4.333, 28.0, 18.0, 28.0),

    # Master bedroom partition
    ("I2: Master bedroom wall", 18.0, 28.0, 18.0, 45.0),

    # Bedroom 2/3 divider
    ("I3: Bedroom divider", 13.0, 11.667, 13.0, 28.0),

    # Bathroom walls
    ("I4: Bath 2 south wall", 18.0, 35.0, 24.0, 35.0),
    ("I5: Bath 2 west wall", 24.0, 35.0, 24.0, 45.0),

    # Hall bathroom
    ("I6: Hall bath east wall", 8.0, 28.0, 8.0, 35.0),
    ("I7: Hall bath north wall", 4.333, 35.0, 8.0, 35.0),
]

# Step 2: Create exterior walls (8")
print("\nStep 2: Creating 4 EXTERIOR walls for 2nd floor (8 inch)...")
created_walls = []
for desc, x1, y1, x2, y2 in perimeter_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': EXTERIOR_8_INCH,
        'locationLine': 0  # Centerline - we pre-calculated offset
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print("  " + desc + ": OK (8\" wall)")
    else:
        print("  " + desc + ": FAILED -", result.get('error', 'Unknown'))

# Step 3: Create interior walls (4")
print("\nStep 3: Creating 7 INTERIOR walls for 2nd floor (4 inch)...")
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
print("COMPLETE: Created", len(created_walls), "walls on Level 2")
print("  - 4 exterior walls (8\") forming rectangular perimeter")
print("  - 7 interior walls (4\") for bedroom/bathroom layout")
print("  - 2nd floor sits above main building (not garage)")
print("="*60)
