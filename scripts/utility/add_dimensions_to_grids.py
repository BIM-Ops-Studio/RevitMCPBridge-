"""
Add Dimension Lines to Grids

This script adds dimension strings to the existing grids:
- Vertical dimension for horizontal grids 1-5 (positioned to the left)
- Horizontal dimension for vertical grids A-D (positioned below)
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
grids = response.get('grids', [])

if not grids:
    print("ERROR: No grids found!")
    exit(1)

# Separate into vertical (A-D) and horizontal (1-5)
vertical_grid_ids = []
horizontal_grid_ids = []

print(f"Found {len(grids)} grids:")
for g in grids:
    name = g['name']
    grid_id = str(g['gridId'])
    start = g.get('startPoint', {})
    end = g.get('endPoint', {})

    # Determine orientation by comparing start/end points
    start_x = start.get('x', 0)
    start_y = start.get('y', 0)
    end_x = end.get('x', 0)
    end_y = end.get('y', 0)

    if abs(start_x - end_x) < 0.1:  # Vertical grid (same X)
        vertical_grid_ids.append(grid_id)
        print(f"  Grid {name} (ID: {grid_id}) - VERTICAL at X={start_x:.2f}")
    else:  # Horizontal grid (same Y)
        horizontal_grid_ids.append(grid_id)
        print(f"  Grid {name} (ID: {grid_id}) - HORIZONTAL at Y={start_y:.2f}")

print(f"\nVertical grids (A-D): {len(vertical_grid_ids)}")
print(f"Horizontal grids (1-5): {len(horizontal_grid_ids)}")

print("\nStep 2: Getting views...")
print("=" * 60)

views_response = call_mcp('getViews', {})
if not views_response.get('success'):
    print(f"ERROR getting views: {views_response.get('error')}")
    print(f"Full response: {json.dumps(views_response, indent=2)}")
    exit(1)

views = views_response.get('views', [])
print(f"Found {len(views)} views")

# Find a floor plan view
view_id = None
for v in views:
    view_type = v.get('viewType', '')
    name = v.get('name', '')
    if 'FloorPlan' in view_type or 'Floor Plan' in name:
        view_id = str(v['viewId'])
        print(f"  Using view: {name} (Type: {view_type}, ID: {view_id})")
        break

if not view_id:
    # Use first view as fallback
    if views:
        view_id = str(views[0]['viewId'])
        print(f"  Using first view: {views[0].get('name')} (ID: {view_id})")
    else:
        print("ERROR: No views found!")
        exit(1)

print("\nStep 3: Adding dimension lines...")
print("=" * 60)

# Add dimensions to vertical grids A-D
if vertical_grid_ids:
    print(f"\nDimensioning vertical grids {vertical_grid_ids}...")
    dim_result = call_mcp('batchDimensionGrids', {
        'viewId': view_id,
        'gridIds': vertical_grid_ids,
        'offset': 5.0,
        'orientation': 'vertical'
    })

    if dim_result.get('success'):
        print(f"  SUCCESS: Created {dim_result.get('dimensionStringsCreated', 0)} dimension string(s)")
        print(f"  Dimension IDs: {dim_result.get('dimensionIds', [])}")
    else:
        print(f"  FAILED: {dim_result.get('error')}")
        print(f"  Full response: {json.dumps(dim_result, indent=2)}")

# Add dimensions to horizontal grids 1-5
if horizontal_grid_ids:
    print(f"\nDimensioning horizontal grids {horizontal_grid_ids}...")
    dim_result = call_mcp('batchDimensionGrids', {
        'viewId': view_id,
        'gridIds': horizontal_grid_ids,
        'offset': 5.0,
        'orientation': 'horizontal'
    })

    if dim_result.get('success'):
        print(f"  SUCCESS: Created {dim_result.get('dimensionStringsCreated', 0)} dimension string(s)")
        print(f"  Dimension IDs: {dim_result.get('dimensionIds', [])}")
    else:
        print(f"  FAILED: {dim_result.get('error')}")
        print(f"  Full response: {json.dumps(dim_result, indent=2)}")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print("\nExpected dimensions:")
print("  Vertical grids A-D (left to right):")
print("    A to B: 7'-0\" (7.0 ft)")
print("    B to C: 17'-8\" (17.667 ft)")
print("    C to D: 13'-8\" (13.667 ft)")
print("    Total: 38'-4\" (38.333 ft)")
print("\n  Horizontal grids 1-5 (top to bottom):")
print("    1 to 2: 12'-1\" (12.083 ft)")
print("    2 to 3: 15'-0\" (15.0 ft)")
print("    3 to 4: 8'-0\" (8.0 ft)")
print("    4 to 5: 15'-0\" (15.0 ft)")
print("    Total: 50'-1\" (50.083 ft)")
