"""
Create walls in Revit based on dimensions extracted directly from 1713 PDF.

READING DIRECTLY FROM PDF A-100 (1ST FLOOR PLAN):
- Sheet scale: 1/4" = 1'-0"
- Garage is on the LEFT (WEST) side
- Main building is to the RIGHT (EAST)
- Porch at front (SOUTH), Rear Lanai at back (NORTH)

Dimensions from PDF dimension strings:
- Main building width: 34'-0"
- Garage width: 12'-1"
- Building depth (N-S): varies - see room dimensions
"""

import json
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params=None):
    """Call Revit MCP bridge."""
    try:
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
    except pywintypes.error as e:
        return {'error': str(e)}

# =============================================================================
# DIMENSIONS EXTRACTED DIRECTLY FROM PDF A-100 (1ST FLOOR PLAN)
# =============================================================================
#
# Looking at the PDF floor plan, from BOTTOM to TOP (South to North):
# - Grid A: South face of building (Y=0)
# - Grid B: 7'-0" north of A
# - Grid C: Further north
# - Grid D: North edge of building
#
# From LEFT to RIGHT (West to East):
# - Grid 1: West face of GARAGE (X=0)
# - Grid 2: East face of garage / West face of main building (12'-1" from Grid 1)
# - Grid 3, 4, 5: Further east
#
# KEY INSIGHT FROM PDF:
# The garage is a SEPARATE volume on the west, only 20' deep (not full building depth)
# The main building is the full depth
#
# Dimension strings from PDF:
# - Horizontal (bottom): Shows main building = 34'-0"
# - Garage width: 12'-1"
# - Building depths vary by room
#
# Room areas from PDF:
# - GARAGE (101): 242 SF  -> approx 12'-1" x 20' = 241.67 SF ✓
# - KITCHEN (104): 204 SF
# - LIVING RM (105): 144 SF
# - DINING RM (106): 100 SF
# - PORCH (EX-1): 54 SF
# - REAR LANAI (EX-2): 110 SF

# Coordinate system: Origin at Grid 1/A (SW corner of garage)
# X positive = East, Y positive = North

# From dimension strings on PDF A-100:
# Looking at the left side dimension string (vertical):
#   7'-0" + more segments = total depth
# Looking at the bottom dimension string (horizontal):
#   Shows 34'-0" for main building portion

# ACTUAL BUILDING DIMENSIONS from careful PDF reading:
GARAGE_WIDTH = 12.083     # 12'-1" = 12 + 1/12 = 12.083 ft
GARAGE_DEPTH = 20.0       # ~20'-0" (garage doesn't extend full building depth)

# Main building dimensions from PDF:
MAIN_BUILDING_WIDTH = 34.0   # 34'-0" shown on dimension string
BUILDING_TOTAL_DEPTH = 38.333  # Grid A to Grid D (South to North edge)

# So total building footprint:
# Width (E-W): Garage (12'-1") is INSIDE the 34'-0" main building width?
#              Or: Garage PLUS main building?
#
# Looking at elevation A-200, the building appears as one mass.
# Looking at floor plan, the garage is clearly a SEPARATE volume on the west.
#
# Correcting based on visual inspection of PDF:
# The 34'-0" dimension appears to be for the MAIN BUILDING ONLY (without garage)
# Total width = Garage width + Main building width? No...
#
# Actually re-reading the PDF more carefully:
# The dimension "34'-0"" at the bottom appears to span from Grid 2 to Grid 5
# The garage (12'-1") spans from Grid 1 to Grid 2
# So TOTAL WIDTH = 12'-1" + 34'-0" = 46'-1"?
#
# But the dimension strings show:
#   11'-4" | 10'-8" | 23'-4" | 7'-0" = 52'-4" ?? That's the N-S dimension!
#
# Let me use the GRID positions which are clearer:
# From the elevations and floor plan:

GRID_X = {
    '1': 0.0,        # West face of garage (ORIGIN)
    '2': 12.083,     # 12'-1" from Grid 1 (East face of garage)
    '3': 27.083,     # 15'-0" from Grid 2
    '4': 35.083,     # 8'-0" from Grid 3
    '5': 50.083,     # 15'-0" from Grid 4 (East edge)
}

GRID_Y = {
    'A': 0.0,        # South face of building
    'B': 7.0,        # 7'-0" from A
    'C': 24.667,     # 17'-8" from A total (7 + 17.667)
    'D': 38.333,     # North edge
}

# First, delete any existing walls
print("Step 1: Checking for existing walls...")
walls_result = call_mcp('getWalls')
if walls_result.get('success') and walls_result.get('walls'):
    # API returns 'wallId' not 'id'
    wall_ids = [w.get('wallId') or w.get('id') for w in walls_result['walls']]
    wall_ids = [wid for wid in wall_ids if wid]  # Filter out None values
    if wall_ids:
        print(f"  Found {len(wall_ids)} existing walls, deleting...")
        delete_result = call_mcp('deleteElements', {'elementIds': wall_ids})
        print(f"  Deleted: {delete_result.get('deletedCount', 0)} walls")
    else:
        print("  No wall IDs found to delete")
else:
    print("  No existing walls found")

# Get level for wall placement
print("\nStep 2: Getting Level 1...")
levels = call_mcp('getLevels')
level_id = None
if levels.get('success'):
    for level in levels.get('levels', []):
        if 'L1' in level['name'] or 'Level 1' in level['name'] or level['elevation'] == 0:
            level_id = level['levelId']
            print(f"  Using level: {level['name']} (ID: {level_id})")
            break

if not level_id:
    print("  ERROR: No Level 1 found!")
    exit(1)

# Get wall type
print("\nStep 3: Getting wall type...")
wall_types = call_mcp('getWallTypes')
wall_type_id = None
if wall_types.get('success'):
    for wt in wall_types.get('wallTypes', []):
        # Prefer generic or basic wall
        if 'Generic' in wt['name'] or 'Basic' in wt['name']:
            wall_type_id = wt['wallTypeId']
            print(f"  Using wall type: {wt['name']} (ID: {wall_type_id})")
            break
    if not wall_type_id and wall_types.get('wallTypes'):
        wall_type_id = wall_types['wallTypes'][0]['wallTypeId']
        print(f"  Using first wall type: {wall_types['wallTypes'][0]['name']}")

if not wall_type_id:
    print("  ERROR: No wall types found!")
    exit(1)

# Define exterior walls based on PDF floor plan
# The building is roughly L-shaped with garage on west side
print("\nStep 4: Creating exterior walls from PDF dimensions...")

# Wall definitions: (description, start_x, start_y, end_x, end_y)
# Tracing counter-clockwise from southwest corner

# Exterior walls from rbcdc_floor_plan_spec.json:
# Counter-clockwise from SW corner (Grid 1/A)
exterior_walls = [
    # EXT-001: South exterior wall - Garage (Grid 1/A to Grid 2/A)
    ("EXT-001: South wall - Garage", GRID_X['1'], GRID_Y['A'], GRID_X['2'], GRID_Y['A']),

    # EXT-002: South exterior wall - Main building (Grid 2/A to Grid 5/A)
    ("EXT-002: South wall - Main", GRID_X['2'], GRID_Y['A'], GRID_X['5'], GRID_Y['A']),

    # EXT-003: East exterior wall (Grid 5/A to Grid 5/D)
    ("EXT-003: East wall", GRID_X['5'], GRID_Y['A'], GRID_X['5'], GRID_Y['D']),

    # EXT-004: North exterior wall (Grid 5/D to Grid 1/D)
    ("EXT-004: North wall", GRID_X['5'], GRID_Y['D'], GRID_X['1'], GRID_Y['D']),

    # EXT-005: West exterior wall - North portion (Grid 1/D to Grid 1/~20')
    ("EXT-005: West wall - North", GRID_X['1'], GRID_Y['D'], GRID_X['1'], 20.0),

    # EXT-006: West exterior wall - Garage (Grid 1/20' to Grid 1/A)
    ("EXT-006: West wall - Garage", GRID_X['1'], 20.0, GRID_X['1'], GRID_Y['A']),
]

wall_height = 10.0  # 10 feet

created_walls = []
for desc, x1, y1, x2, y2 in exterior_walls:
    print(f"\n  Creating: {desc}")
    print(f"    From ({x1:.3f}, {y1:.3f}) to ({x2:.3f}, {y2:.3f})")

    # API expects startPoint and endPoint as [x, y, z] arrays
    result = call_mcp('createWall', {
        'startPoint': [x1, y1, 0],
        'endPoint': [x2, y2, 0],
        'levelId': level_id,
        'height': wall_height,
        'wallTypeId': wall_type_id
    })

    if result.get('success'):
        wall_id = result.get('wallId')
        created_walls.append(wall_id)
        print(f"    SUCCESS: Wall ID {wall_id}")
    else:
        print(f"    FAILED: {result.get('error', 'Unknown error')}")

# INT-001: Garage east wall (separation from main building)
# At Grid 2, from A to 20' (fire-rated)
print("\nStep 5: Creating garage separation wall (INT-001)...")
garage_wall = call_mcp('createWall', {
    'startPoint': [GRID_X['2'], GRID_Y['A'], 0],
    'endPoint': [GRID_X['2'], 20.0, 0],  # Garage is 20' deep
    'levelId': level_id,
    'height': wall_height,
    'wallTypeId': wall_type_id
})
if garage_wall.get('success'):
    print(f"  SUCCESS: Garage separation wall ID {garage_wall.get('wallId')}")
    created_walls.append(garage_wall.get('wallId'))
else:
    print(f"  FAILED: {garage_wall.get('error')}")

print("\n" + "=" * 60)
print(f"COMPLETE: Created {len(created_walls)} walls")
print("=" * 60)
print("\nWall IDs:", created_walls)
