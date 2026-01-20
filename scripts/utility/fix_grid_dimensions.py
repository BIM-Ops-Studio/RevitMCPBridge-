"""
Fix Grid Dimensions - Match the RBCDC Floor Plan Spec

The user's desired orientation:
- Grids A-D are VERTICAL lines (running north-south, positioned left to right)
- Grids 1-5 are HORIZONTAL lines (running east-west, positioned top to bottom)
- Grid 1 at TOP (Y = highest), Grid 5 at BOTTOM (Y = 0)
- Grid A at LEFT (X = 0), Grid D at RIGHT (X = highest)

From the spec file, the CORRECT dimensions are:
  Vertical grids (1-5) spacing: 12'-1", 15'-0", 8'-0", 15'-0" (total 50'-1")
  Horizontal grids (A-D) spacing: 7'-0", 17'-8", 13'-8" (total 38'-4")

Since user wants:
  - A-D as vertical at X positions (using horizontal grid Y values from spec)
  - 1-5 as horizontal at Y positions (using vertical grid X values from spec, inverted)

Correct positions:
  Grid A: X = 0.0
  Grid B: X = 7.0 (7'-0" from A)
  Grid C: X = 24.667 (17'-8" from B, 24'-8" from A)
  Grid D: X = 38.333 (13'-8" from C, 38'-4" from A)

  Grid 1: Y = 50.083 (top - total height)
  Grid 2: Y = 38.0 (12'-1" down from 1)
  Grid 3: Y = 23.0 (15'-0" down from 2)
  Grid 4: Y = 15.0 (8'-0" down from 3)
  Grid 5: Y = 0.0 (15'-0" down from 4, bottom)
"""

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

# STEP 1: Query current grids
print("STEP 1: Querying current grids...")
print("=" * 60)
response = call_mcp('getGrids', {})
current_grids = response.get('grids', [])

print(f"Found {len(current_grids)} grids:")
for g in sorted(current_grids, key=lambda x: x['name']):
    start = g.get('startPoint', {})
    end = g.get('endPoint', {})
    print(f"  Grid {g['name']}: ({start.get('x', 0):.2f}, {start.get('y', 0):.2f}) to ({end.get('x', 0):.2f}, {end.get('y', 0):.2f})")

# STEP 2: Define CORRECT grid positions per spec
print("\n" + "=" * 60)
print("STEP 2: Correct grid positions per spec:")
print("=" * 60)

# VERTICAL grids A-D (left to right)
# Using original horizontal grid Y values as X positions
CORRECT_VERTICAL_GRIDS = {
    'A': 0.0,       # Left edge
    'B': 7.0,       # 7'-0" from A
    'C': 24.667,    # 24'-8" from A (17'-8" from B)
    'D': 38.333,    # 38'-4" from A (13'-8" from C)
}

# HORIZONTAL grids 1-5 (top to bottom)
# Using original vertical grid X values as Y positions, inverted so 1 is at top
CORRECT_HORIZONTAL_GRIDS = {
    '1': 50.083,    # TOP (was Grid 5's X position)
    '2': 38.0,      # 12'-1" down from Grid 1
    '3': 23.0,      # 15'-0" down from Grid 2
    '4': 15.0,      # 8'-0" down from Grid 3
    '5': 0.0,       # BOTTOM - 15'-0" down from Grid 4
}

print("VERTICAL grids A-D (left to right):")
for name, x in sorted(CORRECT_VERTICAL_GRIDS.items()):
    print(f"  Grid {name}: X = {x:.3f} ft")

print("\nHORIZONTAL grids 1-5 (top to bottom):")
for name in ['1', '2', '3', '4', '5']:
    y = CORRECT_HORIZONTAL_GRIDS[name]
    print(f"  Grid {name}: Y = {y:.3f} ft")

# STEP 3: Check if current grids match expected
print("\n" + "=" * 60)
print("STEP 3: Comparing current vs expected...")
print("=" * 60)

current_grid_map = {}
for g in current_grids:
    name = g['name']
    start = g.get('startPoint', {})
    end = g.get('endPoint', {})

    # Determine if vertical or horizontal
    start_x, start_y = start.get('x', 0), start.get('y', 0)
    end_x, end_y = end.get('x', 0), end.get('y', 0)

    # If X values are same, it's vertical; if Y values are same, it's horizontal
    if abs(start_x - end_x) < 0.1:  # Vertical grid
        current_grid_map[name] = {'type': 'vertical', 'position': start_x}
    else:  # Horizontal grid
        current_grid_map[name] = {'type': 'horizontal', 'position': start_y}

# Compare
mismatches = []
for name, expected_x in CORRECT_VERTICAL_GRIDS.items():
    if name in current_grid_map:
        current = current_grid_map[name]
        if current['type'] == 'vertical':
            diff = abs(current['position'] - expected_x)
            if diff > 0.01:
                mismatches.append((name, 'vertical', expected_x, current['position'], diff))
                print(f"  Grid {name}: MISMATCH - Expected X={expected_x:.3f}, Got X={current['position']:.3f} (diff: {diff:.3f} ft)")
            else:
                print(f"  Grid {name}: OK (X={current['position']:.3f})")
        else:
            mismatches.append((name, 'type', 'vertical', current['type'], 0))
            print(f"  Grid {name}: TYPE MISMATCH - Expected vertical, got {current['type']}")
    else:
        mismatches.append((name, 'missing', 0, 0, 0))
        print(f"  Grid {name}: MISSING")

for name, expected_y in CORRECT_HORIZONTAL_GRIDS.items():
    if name in current_grid_map:
        current = current_grid_map[name]
        if current['type'] == 'horizontal':
            diff = abs(current['position'] - expected_y)
            if diff > 0.01:
                mismatches.append((name, 'horizontal', expected_y, current['position'], diff))
                print(f"  Grid {name}: MISMATCH - Expected Y={expected_y:.3f}, Got Y={current['position']:.3f} (diff: {diff:.3f} ft)")
            else:
                print(f"  Grid {name}: OK (Y={current['position']:.3f})")
        else:
            mismatches.append((name, 'type', 'horizontal', current['type'], 0))
            print(f"  Grid {name}: TYPE MISMATCH - Expected horizontal, got {current['type']}")
    else:
        mismatches.append((name, 'missing', 0, 0, 0))
        print(f"  Grid {name}: MISSING")

# STEP 4: Delete and recreate if needed
if mismatches:
    print("\n" + "=" * 60)
    print("STEP 4: Fixing grids...")
    print("=" * 60)

    # Delete all existing grids
    if current_grids:
        grid_ids = [g['gridId'] for g in current_grids]
        print(f"  Deleting {len(grid_ids)} existing grids...")
        result = call_mcp('deleteElements', {'elementIds': grid_ids})
        print(f"  Delete result: {result.get('success', False)}")

    # Grid extents
    x_min, x_max = -5.0, 45.0   # For horizontal grids
    y_min, y_max = -5.0, 55.0   # For vertical grids

    # Create vertical grids A-D
    print("\n  Creating VERTICAL grids A-D:")
    vertical_grid_ids = []
    for name in ['A', 'B', 'C', 'D']:
        x_pos = CORRECT_VERTICAL_GRIDS[name]
        result = create_grid(name, [x_pos, y_min, 0.0], [x_pos, y_max, 0.0])
        if result.get('success'):
            grid_id = result.get('gridId')
            vertical_grid_ids.append(str(grid_id))
            print(f"    Grid {name}: X = {x_pos:.3f} ft - Created (ID: {grid_id})")
        else:
            print(f"    Grid {name}: FAILED - {result.get('error')}")

    # Create horizontal grids 1-5
    print("\n  Creating HORIZONTAL grids 1-5:")
    horizontal_grid_ids = []
    for name in ['1', '2', '3', '4', '5']:
        y_pos = CORRECT_HORIZONTAL_GRIDS[name]
        result = create_grid(name, [x_min, y_pos, 0.0], [x_max, y_pos, 0.0])
        if result.get('success'):
            grid_id = result.get('gridId')
            horizontal_grid_ids.append(str(grid_id))
            print(f"    Grid {name}: Y = {y_pos:.3f} ft - Created (ID: {grid_id})")
        else:
            print(f"    Grid {name}: FAILED - {result.get('error')}")

    # STEP 5: Add dimension lines
    print("\n" + "=" * 60)
    print("STEP 5: Adding dimension lines...")
    print("=" * 60)

    # Get the active view
    views_response = call_mcp('getViews', {})
    view_id = None
    if views_response.get('success') and views_response.get('views'):
        # Find a floor plan view
        for v in views_response['views']:
            if 'Floor Plan' in v.get('name', '') or 'Plan' in v.get('viewType', ''):
                view_id = v['viewId']
                print(f"  Using view: {v['name']} (ID: {view_id})")
                break
        if not view_id:
            view_id = views_response['views'][0]['viewId']
            print(f"  Using first view (ID: {view_id})")

    if view_id and vertical_grid_ids:
        print("\n  Adding dimension to vertical grids A-D...")
        dim_result = call_mcp('batchDimensionGrids', {
            'viewId': str(view_id),
            'gridIds': vertical_grid_ids,
            'offset': 5.0,
            'orientation': 'vertical'
        })
        if dim_result.get('success'):
            print(f"    Dimension created: {dim_result.get('dimensionStringsCreated', 0)} string(s)")
        else:
            print(f"    Failed: {dim_result.get('error')}")

    if view_id and horizontal_grid_ids:
        print("\n  Adding dimension to horizontal grids 1-5...")
        dim_result = call_mcp('batchDimensionGrids', {
            'viewId': str(view_id),
            'gridIds': horizontal_grid_ids,
            'offset': 5.0,
            'orientation': 'horizontal'
        })
        if dim_result.get('success'):
            print(f"    Dimension created: {dim_result.get('dimensionStringsCreated', 0)} string(s)")
        else:
            print(f"    Failed: {dim_result.get('error')}")
else:
    print("\nAll grids are correctly positioned! No changes needed.")

# STEP 6: Final summary
print("\n" + "=" * 60)
print("FINAL GRID LAYOUT:")
print("=" * 60)
print("""
                         Grid D (X = 38.33 ft)
                              |
  Grid 1 (TOP)    ────────────|───────────  Y = 50.083 ft
       |          |           |           |
       |     12'-1" (12.083)  |           |
       |          |           |           |
  Grid 2      ────|───────────|───────────  Y = 38.0 ft
       |          |           |           |
       |     15'-0" (15.0)    |           |
       |          |           |           |
  Grid 3      ────|───────────|───────────  Y = 23.0 ft
       |          |           |           |
       |      8'-0" (8.0)     |           |
       |          |           |           |
  Grid 4      ────|───────────|───────────  Y = 15.0 ft
       |          |           |           |
       |     15'-0" (15.0)    |           |
       |          |           |           |
  Grid 5 (BOTTOM) |───────────|───────────  Y = 0.0 ft
                  |           |
       A          B           C           D
     X=0        X=7       X=24.67     X=38.33

       |<-7'->|<---17'-8"--->|<--13'-8"-->|

Dimension spacing:
  Vertical (A to D):   7'-0" + 17'-8" + 13'-8" = 38'-4" (38.333 ft)
  Horizontal (1 to 5): 12'-1" + 15'-0" + 8'-0" + 15'-0" = 50'-1" (50.083 ft)
""")
