"""
Add Proper Grid Dimension Lines

Creates TWO dimension strings:
1. Horizontal dimension for vertical grids A-D (at the bottom)
2. Vertical dimension for horizontal grids 1-5 (on the left side)
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

print("Adding Proper Grid Dimension Lines")
print("=" * 60)

# Step 1: Get grids and classify them
print("\nStep 1: Getting grids...")
response = call_mcp('getGrids', {})
grids = response.get('grids', [])

vertical_ids = []   # A, B, C, D (grids that run vertically)
horizontal_ids = [] # 1, 2, 3, 4, 5 (grids that run horizontally)

for g in grids:
    name = g['name']
    grid_id = str(g['gridId'])

    # Get full grid info
    detail = call_mcp('getGrid', {'gridId': g['gridId']})
    if detail.get('success'):
        curve = detail.get('curve', {})
        start = curve.get('start', {})
        end = curve.get('end', {})

        dx = abs(end.get('x', 0) - start.get('x', 0))
        dy = abs(end.get('y', 0) - start.get('y', 0))

        if dy > dx:  # Runs more in Y = vertical
            vertical_ids.append(grid_id)
            print(f"  Grid {name} (ID: {grid_id}) - VERTICAL")
        else:  # Runs more in X = horizontal
            horizontal_ids.append(grid_id)
            print(f"  Grid {name} (ID: {grid_id}) - HORIZONTAL")

print(f"\nVertical grids: {len(vertical_ids)}")
print(f"Horizontal grids: {len(horizontal_ids)}")

# Step 2: Get active view
print("\nStep 2: Getting active view...")
active_view = call_mcp('getActiveView', {})
if active_view.get('success'):
    view_id = str(active_view.get('viewId'))
    print(f"  Using view: {active_view.get('viewName')} (ID: {view_id})")
else:
    print(f"  ERROR: {active_view.get('error')}")
    exit(1)

# Step 3: Add dimension for vertical grids (A-D)
print("\nStep 3: Adding dimension for vertical grids A-D...")
if len(vertical_ids) >= 2:
    result = call_mcp('batchDimensionGrids', {
        'viewId': view_id,
        'gridIds': vertical_ids,
        'offset': 5.0,
        'orientation': 'vertical'  # vertical grids get a horizontal dimension line
    })

    if result.get('success'):
        print(f"  SUCCESS: Created {result.get('dimensionStringsCreated', 0)} dimension string")
        print(f"    Dimension IDs: {result.get('dimensionIds', [])}")
    else:
        print(f"  FAILED: {result.get('error')}")
        print(f"  Response: {json.dumps(result, indent=2)}")
else:
    print("  Skipping - need at least 2 vertical grids")

# Step 4: Add dimension for horizontal grids (1-5)
print("\nStep 4: Adding dimension for horizontal grids 1-5...")
if len(horizontal_ids) >= 2:
    result = call_mcp('batchDimensionGrids', {
        'viewId': view_id,
        'gridIds': horizontal_ids,
        'offset': 5.0,
        'orientation': 'horizontal'  # horizontal grids get a vertical dimension line
    })

    if result.get('success'):
        print(f"  SUCCESS: Created {result.get('dimensionStringsCreated', 0)} dimension string")
        print(f"    Dimension IDs: {result.get('dimensionIds', [])}")
    else:
        print(f"  FAILED: {result.get('error')}")
        print(f"  Response: {json.dumps(result, indent=2)}")
else:
    print("  Skipping - need at least 2 horizontal grids")

print("\n" + "=" * 60)
print("DONE!")
print("\nYou should now see dimension lines on your grids:")
print("  - HORIZONTAL dimension below the vertical grids (A-D)")
print("    Should show: 7'-0\", 17'-8\", 13'-8\"")
print("  - VERTICAL dimension to the left of horizontal grids (1-5)")
print("    Should show: 12'-1\", 15'-0\", 8'-0\", 15'-0\"")
print("=" * 60)
