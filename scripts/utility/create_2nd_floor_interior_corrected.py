"""
Create corrected 2nd floor interior walls matching the PDF layout.

CRITICAL ORIENTATION MAPPING (discovered through user feedback):
- PDF LEFT (garage side) = Revit SOUTH (low Y values)
- PDF RIGHT = Revit NORTH (high Y values)
- PDF BOTTOM = Revit WEST (low X values)
- PDF TOP = Revit EAST (high X values)

This is a 90° clockwise rotation from PDF to Revit coordinates.

Building dimensions (from 1st floor exterior walls):
- X range: 0 to 50.083 ft (west to east in Revit)
- Y range: 0 to 38.333 ft (south to north in Revit)
- Garage: X=0 to 12.083, Y=0 to 20.0

2nd Floor Layout from PDF A-100 (page 5):
Rooms are arranged with:
- Balcony on the right side (PDF) = NORTH side in Revit (high Y)
- Bedrooms 200, 202 on top-left (PDF) = EAST-SOUTH in Revit
- M/Bedroom 205 on right (PDF) = NORTH in Revit
- Stairs/hallway in center-left (PDF) = CENTER-SOUTH in Revit

Key dimensions from PDF:
- Overall 2nd floor: 34'-0" x 41'-0" (excluding balcony)
- Balcony: 14'-0" x 7'-11 3/4"

Wall type IDs from Revit:
- EXTERIOR_8_INCH = 441451 (for reference)
- INTERIOR_4_INCH = 441518
"""

import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Wall type IDs
EXTERIOR_8_INCH = 441451
INTERIOR_4_INCH = 441518

# Level 2 ID
LEVEL_2_ID = 9946

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

def create_wall(wall_id, start_x, start_y, end_x, end_y, wall_type, description):
    """Create a wall with the given parameters."""
    # Wall height for 2nd floor (floor-to-floor height is 10 ft per PDF)
    height = 10.0

    # MCP expects startPoint and endPoint as [x, y, z] arrays
    params = {
        'startPoint': [start_x, start_y, 0.0],
        'endPoint': [end_x, end_y, 0.0],
        'levelId': LEVEL_2_ID,
        'wallTypeId': wall_type,
        'height': height
    }

    print(f"\nCreating {wall_id}: {description}")
    print(f"  Start: ({start_x:.3f}, {start_y:.3f})")
    print(f"  End: ({end_x:.3f}, {end_y:.3f})")

    result = call_mcp('createWall', params)

    if result.get('success'):
        print(f"  SUCCESS - Wall ID: {result.get('wallId')}")
        return result.get('wallId')
    else:
        print(f"  ERROR: {result.get('error')}")
        return None

# ============================================================================
# 2ND FLOOR INTERIOR WALLS
# ============================================================================
# Reference points from exterior perimeter (already created):
# - Building: X=12.083 to 50.083 (main building without garage)
# - Building: Y=0 to 38.333
# - 2nd floor sits above 1st floor main building only (no garage above)
#
# From PDF dimensions on 2nd floor plan:
# Grid lines: 1,2,3,4,5 (vertical/X) and A,B,C,D (horizontal/Y)
#
# Reading the 2nd floor plan dimensions:
# - From left edge to stair wall: varies
# - Hallway width: ~4'-0"
# - Bedroom depths: ~9'-5 3/4" and ~9'-5 3/4"
# - M/Bedroom width: ~16'-0 1/2"
# - Closet depths: vary
# ============================================================================

print("=" * 60)
print("CREATING 2ND FLOOR INTERIOR WALLS")
print("=" * 60)

# Interior wall thickness offset (4" = 0.333 ft, half = 0.167 ft)
INT_OFFSET = 0.167

# Define wall coordinates based on PDF dimensions
# Converting PDF coordinates to Revit with 90° rotation

interior_walls = []

# ============================================================================
# HALLWAY AND CIRCULATION WALLS
# ============================================================================

# The hallway runs roughly north-south in Revit (left-right in PDF)
# From the PDF, the hallway is between the bedrooms and the baths/M.Bedroom

# Wall INT-201: East wall of Hallway 208 (separates hallway from Bedroom 200/202)
# This runs north-south in Revit
# Position: approximately X = 23.0 (from PDF dimensions)
interior_walls.append({
    'id': 'INT-201',
    'description': 'Hallway east wall (bedrooms side)',
    'start': (23.0, 7.0),   # Start at south
    'end': (23.0, 26.0),     # End at north
    'type': INTERIOR_4_INCH
})

# Wall INT-202: West wall of Hallway 208 (separates hallway from baths/stairs)
# Position: approximately X = 19.0
interior_walls.append({
    'id': 'INT-202',
    'description': 'Hallway west wall (bath/stair side)',
    'start': (19.0, 7.0),
    'end': (19.0, 26.0),
    'type': INTERIOR_4_INCH
})

# ============================================================================
# BEDROOM 200 AND 202 WALLS
# ============================================================================

# Wall INT-203: Wall between Bedroom 200 and Bedroom 202
# This runs east-west in Revit (top-bottom in PDF)
# Position: approximately Y = 16.5 (midpoint between bedrooms)
interior_walls.append({
    'id': 'INT-203',
    'description': 'Wall between Bedroom 200 and 202',
    'start': (23.0, 16.5),
    'end': (35.0, 16.5),
    'type': INTERIOR_4_INCH
})

# Wall INT-204: Closet 201 wall (in Bedroom 200)
# Small closet partition
interior_walls.append({
    'id': 'INT-204',
    'description': 'Closet 201 wall',
    'start': (31.0, 23.0),
    'end': (35.0, 23.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-205: Closet 201 return wall
interior_walls.append({
    'id': 'INT-205',
    'description': 'Closet 201 return wall',
    'start': (31.0, 23.0),
    'end': (31.0, 26.0),
    'type': INTERIOR_4_INCH
})

# ============================================================================
# BATHROOM WALLS (203, 204, 206)
# ============================================================================

# Wall INT-206: LAV/SHOWER 203 south wall
interior_walls.append({
    'id': 'INT-206',
    'description': 'LAV/SHOWER 203 south wall',
    'start': (12.083, 16.0),
    'end': (19.0, 16.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-207: LAV/SHOWER 203 east wall
interior_walls.append({
    'id': 'INT-207',
    'description': 'LAV/SHOWER 203 east wall',
    'start': (19.0, 16.0),
    'end': (19.0, 23.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-208: BATH 204 wall (between 203 and 204)
interior_walls.append({
    'id': 'INT-208',
    'description': 'Wall between LAV/SHOWER 203 and BATH 204',
    'start': (12.083, 23.0),
    'end': (19.0, 23.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-209: BATH 206 south wall (in M/Bedroom area)
interior_walls.append({
    'id': 'INT-209',
    'description': 'BATH 206 south wall',
    'start': (35.0, 7.0),
    'end': (42.0, 7.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-210: BATH 206 north wall
interior_walls.append({
    'id': 'INT-210',
    'description': 'BATH 206 north wall',
    'start': (35.0, 13.0),
    'end': (42.0, 13.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-211: BATH 206 east wall
interior_walls.append({
    'id': 'INT-211',
    'description': 'BATH 206 east wall',
    'start': (42.0, 7.0),
    'end': (42.0, 13.0),
    'type': INTERIOR_4_INCH
})

# ============================================================================
# M/BEDROOM 205 WALLS
# ============================================================================

# Wall INT-212: Closet 211 wall (M/Bedroom closet)
interior_walls.append({
    'id': 'INT-212',
    'description': 'Closet 211 wall',
    'start': (42.0, 7.0),
    'end': (50.083, 7.0),
    'type': INTERIOR_4_INCH
})

# ============================================================================
# STUDY 207 AND CLOSET WALLS
# ============================================================================

# Wall INT-213: Study 207 north wall
interior_walls.append({
    'id': 'INT-213',
    'description': 'Study 207 north wall',
    'start': (12.083, 7.0),
    'end': (19.0, 7.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-214: Closet 209 wall
interior_walls.append({
    'id': 'INT-214',
    'description': 'Closet 209 wall',
    'start': (23.0, 7.0),
    'end': (28.0, 7.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-215: Closet 209 return
interior_walls.append({
    'id': 'INT-215',
    'description': 'Closet 209 return wall',
    'start': (28.0, 7.0),
    'end': (28.0, 10.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-216: Closet 210 wall (small closet)
interior_walls.append({
    'id': 'INT-216',
    'description': 'Closet 210 wall',
    'start': (28.0, 10.0),
    'end': (31.0, 10.0),
    'type': INTERIOR_4_INCH
})

# Wall INT-217: Chase C2 wall
interior_walls.append({
    'id': 'INT-217',
    'description': 'Chase C2 wall',
    'start': (31.0, 7.0),
    'end': (31.0, 10.0),
    'type': INTERIOR_4_INCH
})

# ============================================================================
# CREATE ALL WALLS
# ============================================================================

print(f"\nTotal interior walls to create: {len(interior_walls)}")
print("-" * 60)

created_walls = []
failed_walls = []

for wall in interior_walls:
    wall_id = create_wall(
        wall['id'],
        wall['start'][0],
        wall['start'][1],
        wall['end'][0],
        wall['end'][1],
        wall['type'],
        wall['description']
    )

    if wall_id:
        created_walls.append(wall['id'])
    else:
        failed_walls.append(wall['id'])

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Successfully created: {len(created_walls)} walls")
print(f"Failed: {len(failed_walls)} walls")

if failed_walls:
    print(f"\nFailed walls: {failed_walls}")

print("\n2nd floor interior walls creation complete!")
print("Please verify in Revit that rooms match PDF layout:")
print("  - BEDROOM 200 (97 SF) - east-south area")
print("  - BEDROOM 202 (99 SF) - east-center area")
print("  - M/BEDROOM 205 (164 SF) - north-east area")
print("  - HALLWAY 208 (62 SF) - central corridor")
print("  - LAV/SHOWER 203, BATH 204, BATH 206")
print("  - STUDY 207, CLOSETS 209, 210, 211")
