"""
Add Grid Dimension Lines V2
Uses the correct response parsing from getGrids and gets active view
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

print("Step 1: Getting current grids...")
print("=" * 60)

response = call_mcp('getGrids', {})
print(f"Raw response: {json.dumps(response, indent=2)[:500]}...")

grids = response.get('grids', [])

if not grids:
    print("ERROR: No grids found!")
    exit(1)

# The getGrids response has 'curve' object with 'start' and 'end'
# (not 'startPoint' and 'endPoint')
vertical_grid_ids = []
horizontal_grid_ids = []

print(f"\nFound {len(grids)} grids:")
for g in grids:
    name = g['name']
    grid_id = str(g['gridId'])
    curve = g.get('curve', {})

    # Get start and end from the curve object
    start = curve.get('start', {})
    end = curve.get('end', {})

    start_x = start.get('x', 0)
    start_y = start.get('y', 0)
    end_x = end.get('x', 0)
    end_y = end.get('y', 0)

    # Determine if vertical or horizontal based on which direction it runs
    dx = abs(end_x - start_x)
    dy = abs(end_y - start_y)

    if dy > dx:  # Runs more in Y direction = vertical line (constant X)
        vertical_grid_ids.append(grid_id)
        print(f"  Grid {name} (ID: {grid_id}) - VERTICAL at X={start_x:.2f}")
    else:  # Runs more in X direction = horizontal line (constant Y)
        horizontal_grid_ids.append(grid_id)
        print(f"  Grid {name} (ID: {grid_id}) - HORIZONTAL at Y={start_y:.2f}")

print(f"\nVertical grids: {len(vertical_grid_ids)} IDs: {vertical_grid_ids}")
print(f"Horizontal grids: {len(horizontal_grid_ids)} IDs: {horizontal_grid_ids}")

print("\nStep 2: Getting active view...")
print("=" * 60)

# Try getActiveView first
active_view_response = call_mcp('getActiveView', {})
print(f"getActiveView response: {json.dumps(active_view_response, indent=2)}")

view_id = None
if active_view_response.get('success'):
    view_id = str(active_view_response.get('viewId'))
    print(f"  Using active view ID: {view_id}")
else:
    # Fallback to getViews
    print("  getActiveView failed, trying getViews...")
    views_response = call_mcp('getViews', {})
    print(f"  getViews response: {json.dumps(views_response, indent=2)[:300]}...")

    views = views_response.get('views', [])
    if views:
        # Find a floor plan view
        for v in views:
            view_type = v.get('viewType', '')
            name = v.get('name', '')
            if 'FloorPlan' in view_type or 'Floor Plan' in name or 'Level' in name:
                view_id = str(v['viewId'])
                print(f"  Using view: {name} (ID: {view_id})")
                break

        if not view_id:
            view_id = str(views[0]['viewId'])
            print(f"  Using first available view (ID: {view_id})")

if not view_id:
    print("ERROR: Could not get a view ID!")
    print("Trying to create dimensions without view ID (will use active)...")

print("\nStep 3: Adding dimension lines...")
print("=" * 60)

# Add dimensions to vertical grids (A-D)
if vertical_grid_ids and len(vertical_grid_ids) >= 2:
    print(f"\nDimensioning {len(vertical_grid_ids)} vertical grids...")
    params = {
        'gridIds': vertical_grid_ids,
        'offset': 5.0,
        'orientation': 'vertical'
    }
    if view_id:
        params['viewId'] = view_id

    dim_result = call_mcp('batchDimensionGrids', params)

    if dim_result.get('success'):
        print(f"  SUCCESS: Created {dim_result.get('dimensionStringsCreated', 0)} dimension string(s)")
    else:
        print(f"  FAILED: {dim_result.get('error')}")
        print(f"  Full response: {json.dumps(dim_result, indent=2)}")
else:
    print(f"  Skipping vertical grids - need at least 2, have {len(vertical_grid_ids)}")

# Add dimensions to horizontal grids (1-5)
if horizontal_grid_ids and len(horizontal_grid_ids) >= 2:
    print(f"\nDimensioning {len(horizontal_grid_ids)} horizontal grids...")
    params = {
        'gridIds': horizontal_grid_ids,
        'offset': 5.0,
        'orientation': 'horizontal'
    }
    if view_id:
        params['viewId'] = view_id

    dim_result = call_mcp('batchDimensionGrids', params)

    if dim_result.get('success'):
        print(f"  SUCCESS: Created {dim_result.get('dimensionStringsCreated', 0)} dimension string(s)")
    else:
        print(f"  FAILED: {dim_result.get('error')}")
        print(f"  Full response: {json.dumps(dim_result, indent=2)}")
else:
    print(f"  Skipping horizontal grids - need at least 2, have {len(horizontal_grid_ids)}")

print("\n" + "=" * 60)
print("Expected grid dimensions:")
print("  Vertical grids A-D (spacing):")
print("    A to B: 7'-0\" (7.0 ft)")
print("    B to C: 17'-8\" (17.667 ft)")
print("    C to D: 13'-8\" (13.667 ft)")
print("  Horizontal grids 1-5 (spacing):")
print("    1 to 2: 12'-1\" (12.083 ft)")
print("    2 to 3: 15'-0\" (15.0 ft)")
print("    3 to 4: 8'-0\" (8.0 ft)")
print("    4 to 5: 15'-0\" (15.0 ft)")
print("=" * 60)
