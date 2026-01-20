import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def call_mcp(method, params):
    handle = win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )
    request = {'method': method, 'params': params}
    win32file.WriteFile(handle, (json.dumps(request) + '\n').encode('utf-8'))
    response_data = b''
    while True:
        result, chunk = win32file.ReadFile(handle, 64*1024)
        response_data += chunk
        if b'\n' in chunk or len(chunk) == 0:
            break
    win32file.CloseHandle(handle)
    return json.loads(response_data.decode('utf-8').strip())

def create_grid(name, start, end):
    return call_mcp('createGrid', {
        'name': name,
        'startPoint': start,
        'endPoint': end
    })

# Step 1: Delete ALL existing grids
print("Step 1: Getting and deleting all existing grids...")
response = call_mcp('getGrids', {})
grids = response.get('grids', [])
if grids:
    grid_ids = [g['gridId'] for g in grids]
    print(f"  Deleting {len(grid_ids)} grids...")
    result = call_mcp('deleteElements', {'elementIds': grid_ids})
    print(f"  Delete result: {result.get('success', False)}")
else:
    print("  No grids to delete")

# Step 2: Create grids with CORRECT dimensions from the floor plan spec
#
# YOUR DESIRED ORIENTATION:
# - Grids A-D are VERTICAL (running top to bottom, positioned left to right)
# - Grids 1-5 are HORIZONTAL (running left to right, positioned top to bottom)
# - Grid 1 at TOP, Grid 5 at BOTTOM
# - Grid A at LEFT, Grid D at RIGHT
#
# From the spec, the ORIGINAL dimensions were:
# Vertical grids 1-5 at X = 0, 12.083, 27.083, 35.083, 50.083
# Horizontal grids A-D at Y = 0, 7.0, 24.667, 38.333
#
# Mapping to your orientation:
# A-D become vertical at X positions (from original horizontal Y values)
# 1-5 become horizontal at Y positions (from original vertical X values, but INVERTED for 1 at top)

print("\nStep 2: Creating grids with correct dimensions...")

# VERTICAL grids A-D (left to right) - using original horizontal grid Y values as X
# A at left (X=0), D at right (X=38.333)
vertical_grids = [
    ('A', 0.0),       # Left edge
    ('B', 7.0),       # 7'-0" from A
    ('C', 24.667),    # 24'-8" from A (17'-8" from B)
    ('D', 38.333),    # 38'-4" from A (13'-8" from C)
]

# HORIZONTAL grids 1-5 (top to bottom) - using original vertical grid X values as Y, INVERTED
# Original X positions: 1=0, 2=12.083, 3=27.083, 4=35.083, 5=50.083
# Inverted (1 at top = highest Y):
# Grid 1: Y = 50.083 (top)
# Grid 2: Y = 50.083 - 12.083 = 38.0
# Grid 3: Y = 50.083 - 27.083 = 23.0
# Grid 4: Y = 50.083 - 35.083 = 15.0
# Grid 5: Y = 0 (bottom)

# Actually, let's keep the SPACING correct from the spec:
# Between 1-2: 12'-1" (12.083)
# Between 2-3: 15'-0" (15.0)
# Between 3-4: 8'-0" (8.0)
# Between 4-5: 15'-0" (15.0)
# Total: 50'-1" (50.083)

horizontal_grids = [
    ('1', 50.083),    # TOP (was Grid 5 position)
    ('2', 38.0),      # 12'-1" down from Grid 1 (50.083 - 12.083)
    ('3', 23.0),      # 15'-0" down from Grid 2 (38.0 - 15.0)
    ('4', 15.0),      # 8'-0" down from Grid 3 (23.0 - 8.0)
    ('5', 0.0),       # BOTTOM - 15'-0" down from Grid 4
]

# Grid extents
x_min, x_max = -5.0, 45.0   # For horizontal grids
y_min, y_max = -5.0, 55.0   # For vertical grids

print("\nCreating VERTICAL grids A-D (left to right):")
print("=" * 50)
vertical_grid_ids = []
for name, x_pos in vertical_grids:
    result = create_grid(name, [x_pos, y_min, 0.0], [x_pos, y_max, 0.0])
    if result.get('success'):
        grid_id = result.get('gridId')
        vertical_grid_ids.append(grid_id)
        print(f"  Grid {name}: X = {x_pos} ft - Created (ID: {grid_id})")
    else:
        print(f"  Grid {name}: FAILED - {result.get('error')}")

print("\nCreating HORIZONTAL grids 1-5 (top to bottom):")
print("=" * 50)
horizontal_grid_ids = []
for name, y_pos in horizontal_grids:
    result = create_grid(name, [x_min, y_pos, 0.0], [x_max, y_pos, 0.0])
    if result.get('success'):
        grid_id = result.get('gridId')
        horizontal_grid_ids.append(grid_id)
        print(f"  Grid {name}: Y = {y_pos} ft - Created (ID: {grid_id})")
    else:
        print(f"  Grid {name}: FAILED - {result.get('error')}")

# Step 3: Create dimension lines between grids
print("\nStep 3: Creating dimension lines...")

# Get level for dimensions
levels_response = call_mcp('getLevels', {})
level_id = None
if levels_response.get('success') and levels_response.get('levels'):
    level_id = levels_response['levels'][0]['levelId']
    print(f"  Using level: {levels_response['levels'][0]['name']} (ID: {level_id})")

if level_id:
    # Create horizontal dimension string for vertical grids A-D (along bottom)
    # Points for dimension at Y = -3 (below grids)
    dim_y = -3.0
    vertical_dim_points = [[x, dim_y, 0.0] for name, x in vertical_grids]

    print("\n  Creating dimension for vertical grids A-D...")
    dim_result = call_mcp('createDimension', {
        'points': vertical_dim_points,
        'viewId': None,  # Use active view
        'dimensionType': 'Linear'
    })
    if dim_result.get('success'):
        print(f"    Dimension created (ID: {dim_result.get('dimensionId')})")
    else:
        print(f"    Failed: {dim_result.get('error')}")

    # Create vertical dimension string for horizontal grids 1-5 (along left side)
    # Points for dimension at X = -3 (left of grids)
    dim_x = -3.0
    horizontal_dim_points = [[dim_x, y, 0.0] for name, y in horizontal_grids]

    print("\n  Creating dimension for horizontal grids 1-5...")
    dim_result = call_mcp('createDimension', {
        'points': horizontal_dim_points,
        'viewId': None,
        'dimensionType': 'Linear'
    })
    if dim_result.get('success'):
        print(f"    Dimension created (ID: {dim_result.get('dimensionId')})")
    else:
        print(f"    Failed: {dim_result.get('error')}")

print("\n" + "=" * 50)
print("FINAL GRID LAYOUT:")
print("=" * 50)
print("""
  Grid 1 (TOP)    ────────────────────────────────  Y = 50.08 ft
       │                                       │
       │     12'-1"                            │
       │                                       │
  Grid 2      ────────────────────────────────────  Y = 38.0 ft
       │                                       │
       │     15'-0"                            │
       │                                       │
  Grid 3      ────────────────────────────────────  Y = 23.0 ft
       │                                       │
       │      8'-0"                            │
       │                                       │
  Grid 4      ────────────────────────────────────  Y = 15.0 ft
       │                                       │
       │     15'-0"                            │
       │                                       │
  Grid 5 (BOTTOM) ────────────────────────────────  Y = 0.0 ft
       A     B          C              D
     X=0   X=7       X=24.67       X=38.33
       |<-7'->|<--17'-8"-->|<--13'-8"-->|
""")
