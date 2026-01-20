"""
Create RBCDC 2nd floor INTERIOR walls - CORRECTED based on PDF dimensions.

Based on careful reading of the 2ND FLOOR plan (A-100, page 5):
- The 2nd floor footprint is 34'-0" wide by ~33'-4" deep
- Grid lines: 1, 2, 3, 4, 5 (vertical) and A, B, C, D (horizontal)

Existing 2nd floor exterior walls (CORRECT - don't touch):
- X range: 4.333 to 28.333 (24 ft)
- Y range: 11.667 to 45.0 (33.333 ft)

Interior walls need to create these rooms:
- 200 BEDROOM (97 SF) - southwest
- 201 CLOSET (12 SF) - attached to 200
- 202 BEDROOM (99 SF) - south center
- 203 LAV/SHOWER (39 SF) - between bedrooms
- 204 BATH (32 SF) - center (cased opening)
- 205 M/BEDROOM (164 SF) - northwest
- 206 BATH (39 SF) - master bath
- 207 STUDY (28 SF) - northeast above stairs
- 208 HALLWAY (62 SF) - central corridor
- 209 CLOSET (12 SF)
- 210 CLOSET (4 SF)
- 211 CLOSET (28 SF) - master closet
- C2 CHASE (3 SF) - plumbing chase

From PDF dimensions:
- Top row across: 2'-0", 2'-8", 2'-8", 2'-8", 4'-8", 2'-8", 2'-8", 2'-8", 2'-0"
- Grid spacing: 11'-4", 10'-8", varies
- Room heights from plan: 9'-5 3/4" typical for bedrooms
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
INTERIOR_4_INCH = 441518  # Generic - 4"

# Step 1: Get Level 2
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

# Step 2: Delete ONLY interior walls on Level 2
print("\nStep 2: Getting current walls on Level 2 to delete interior walls...")
walls_result = call_mcp('getWalls')
interior_wall_ids = []
if walls_result.get('success') and walls_result.get('walls'):
    for w in walls_result['walls']:
        # Check if it's on Level 2 and is an interior wall (4" thickness)
        if w.get('levelId') == level_id:
            # Interior walls are typically 4" = 0.333 ft thick
            # We'll identify by position - interior walls are not on the perimeter
            wall_id = w.get('wallId')
            # For safety, let's check wall type or just delete all Level 2 walls except perimeter
            # Actually, let's be more precise - get wall geometry
            start = w.get('startPoint', {})
            end = w.get('endPoint', {})

            # Perimeter coordinates (exterior walls we want to KEEP):
            # X: 4.333 or 28.333 (east/west walls)
            # Y: 11.667 or 45.0 (south/north walls)

            is_perimeter = False
            x1, y1 = start.get('x', 0), start.get('y', 0)
            x2, y2 = end.get('x', 0), end.get('y', 0)

            # Check if wall is on perimeter (within tolerance)
            tol = 0.5
            if (abs(x1 - 4.333) < tol and abs(x2 - 4.333) < tol) or \
               (abs(x1 - 28.333) < tol and abs(x2 - 28.333) < tol) or \
               (abs(y1 - 11.667) < tol and abs(y2 - 11.667) < tol) or \
               (abs(y1 - 45.0) < tol and abs(y2 - 45.0) < tol):
                is_perimeter = True

            if not is_perimeter and wall_id:
                interior_wall_ids.append(wall_id)
                print(f"  Will delete interior wall {wall_id}: ({x1:.1f},{y1:.1f}) to ({x2:.1f},{y2:.1f})")

if interior_wall_ids:
    delete_result = call_mcp('deleteElements', {'elementIds': interior_wall_ids})
    print(f"  Deleted {delete_result.get('deletedCount', 0)} interior walls")
else:
    print("  No interior walls found to delete")

wall_height = 10.0  # 2nd floor height

# ============================================================================
# 2ND FLOOR INTERIOR WALLS - Based on PDF A-100 2ND FLOOR PLAN
#
# The 2nd floor boundary:
# - West wall: X = 4.333
# - East wall: X = 28.333
# - South wall: Y = 11.667
# - North wall: Y = 45.0
#
# Reading from PDF, the layout shows:
# - Hallway runs E-W through the center
# - Master bedroom (205) in NW corner with bath (206) and closet (211)
# - Two bedrooms (200, 202) on the south
# - Bathroom (204) and Lav/Shower (203) between south bedrooms
# - Study (207) in NE corner above stairs
# - Stairs come up in the NE area
#
# Key Y coordinates from PDF (bottom to top):
# - Y = 11.667: South exterior wall
# - Y ~ 21.0: South wall of hallway (separates bedrooms from hall)
# - Y ~ 28.0: North wall of hallway
# - Y = 45.0: North exterior wall
#
# Key X coordinates from PDF (left to right):
# - X = 4.333: West exterior wall
# - X ~ 13.5: Wall between bedroom 200 and bathroom area
# - X ~ 18.0: Wall between bathroom and bedroom 202
# - X ~ 22.0: East wall of bedroom 202 / study area
# - X = 28.333: East exterior wall
# ============================================================================

# From PDF measurements (converting to feet):
# 9'-5 3/4" = 9.479 ft (typical bedroom width/depth)
# 12'-0 1/2" = 12.042 ft
# 16'-0 1/2" = 16.042 ft

# Let me recalculate based on the 2nd floor being 24' wide (28.333 - 4.333)
# and 33.333' tall (45.0 - 11.667)

# Interior walls based on careful PDF reading:
interior_walls = [
    # HALLWAY walls (E-W corridor through center)
    # South wall of hallway at approximately Y=21 (from grid B area)
    ("Hallway south wall (west section)", 4.333, 21.0, 13.0, 21.0),
    ("Hallway south wall (east section)", 18.0, 21.0, 22.0, 21.0),

    # North wall of hallway at approximately Y=28
    ("Hallway north wall", 4.333, 28.0, 22.0, 28.0),

    # BEDROOM 200 (SW corner) - separated from bath area
    # East wall of bedroom 200
    ("Bedroom 200 east wall", 13.0, 11.667, 13.0, 21.0),

    # Closet 201 wall (inside bedroom 200)
    ("Closet 201 south wall", 4.333, 14.5, 7.0, 14.5),
    ("Closet 201 east wall", 7.0, 11.667, 7.0, 14.5),

    # LAV/SHOWER 203 and BATH 204 area (center south)
    # West wall of lav/shower
    ("Lav/Shower 203 west wall", 13.0, 11.667, 13.0, 18.0),
    # East wall of lav/shower (separates from bath 204)
    ("Lav/Shower 203 east wall", 15.5, 11.667, 15.5, 18.0),
    # North wall of bath area
    ("Bath area north wall", 13.0, 18.0, 18.0, 18.0),

    # BEDROOM 202 - south center/east
    ("Bedroom 202 west wall", 18.0, 11.667, 18.0, 21.0),

    # Closet 209 (in bedroom 200 area, north side)
    ("Closet 209 south wall", 4.333, 18.0, 7.0, 18.0),
    ("Closet 209 east wall", 7.0, 18.0, 7.0, 21.0),

    # MASTER BEDROOM 205 area (NW)
    # East wall of master bedroom
    ("M/Bedroom 205 east wall", 18.0, 28.0, 18.0, 45.0),

    # BATH 206 (master bath)
    ("Bath 206 south wall", 18.0, 37.0, 24.0, 37.0),
    ("Bath 206 east wall", 24.0, 37.0, 24.0, 45.0),

    # CLOSET 211 (master closet)
    ("Closet 211 south wall", 4.333, 35.0, 10.0, 35.0),
    ("Closet 211 east wall", 10.0, 35.0, 10.0, 45.0),

    # STUDY 207 (NE corner above stairs)
    ("Study 207 west wall", 22.0, 28.0, 22.0, 35.0),
    ("Study 207 north wall", 22.0, 35.0, 28.333, 35.0),

    # CHASE C2 (plumbing chase between baths)
    ("Chase C2 west wall", 17.0, 18.0, 17.0, 21.0),
    ("Chase C2 north wall", 15.5, 21.0, 17.0, 21.0),
]

# Step 3: Create interior walls (4")
print(f"\nStep 3: Creating {len(interior_walls)} INTERIOR walls for 2nd floor (4 inch)...")
created_walls = []
for desc, x1, y1, x2, y2 in interior_walls:
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': INTERIOR_4_INCH,
        'locationLine': 0  # Centerline
    })
    if result.get('success'):
        created_walls.append(result.get('wallId'))
        print(f"  {desc}: OK")
    else:
        print(f"  {desc}: FAILED - {result.get('error', 'Unknown')}")

print("\n" + "="*60)
print(f"COMPLETE: Created {len(created_walls)} interior walls on Level 2")
print("  Room layout should now match PDF:")
print("    - Bedrooms 200, 202 on south side")
print("    - Hallway 208 running E-W through center")
print("    - Master bedroom 205 in NW with bath 206 and closet 211")
print("    - Bathrooms 203, 204 between south bedrooms")
print("    - Study 207 in NE corner")
print("="*60)
