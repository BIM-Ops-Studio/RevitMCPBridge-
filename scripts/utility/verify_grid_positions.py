"""
Verify Grid Positions - Query each grid individually to get curve data
and compare against expected values from the spec
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

# Expected positions from spec (after transformation)
EXPECTED = {
    # Vertical grids A-D (constant X, run in Y direction)
    'A': {'type': 'vertical', 'position': 0.0},
    'B': {'type': 'vertical', 'position': 7.0},
    'C': {'type': 'vertical', 'position': 24.667},
    'D': {'type': 'vertical', 'position': 38.333},
    # Horizontal grids 1-5 (constant Y, run in X direction)
    '1': {'type': 'horizontal', 'position': 50.083},
    '2': {'type': 'horizontal', 'position': 38.0},
    '3': {'type': 'horizontal', 'position': 23.0},
    '4': {'type': 'horizontal', 'position': 15.0},
    '5': {'type': 'horizontal', 'position': 0.0},
}

print("Verifying Grid Positions")
print("=" * 70)

# Get all grids first
response = call_mcp('getGrids', {})
grids = response.get('grids', [])

print(f"Found {len(grids)} grids. Querying each individually...\n")

results = []
for g in grids:
    name = g['name']
    grid_id = g['gridId']

    # Get individual grid details
    detail = call_mcp('getGrid', {'gridId': grid_id})

    if detail.get('success'):
        curve = detail.get('curve', {})
        start = curve.get('start', {})
        end = curve.get('end', {})

        start_x = start.get('x', 0)
        start_y = start.get('y', 0)
        end_x = end.get('x', 0)
        end_y = end.get('y', 0)

        # Determine type and position
        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)

        if dy > dx:  # Runs more in Y = vertical line (constant X)
            actual_type = 'vertical'
            actual_position = start_x
        else:  # Runs more in X = horizontal line (constant Y)
            actual_type = 'horizontal'
            actual_position = start_y

        # Compare to expected
        expected = EXPECTED.get(name, {})
        expected_type = expected.get('type', '?')
        expected_pos = expected.get('position', 0)

        type_match = actual_type == expected_type
        pos_diff = abs(actual_position - expected_pos)
        pos_match = pos_diff < 0.01

        status = "OK" if (type_match and pos_match) else "MISMATCH"

        results.append({
            'name': name,
            'actual_type': actual_type,
            'actual_pos': actual_position,
            'expected_type': expected_type,
            'expected_pos': expected_pos,
            'type_match': type_match,
            'pos_match': pos_match,
            'status': status
        })

        print(f"Grid {name:2}: {actual_type:10} at {actual_position:8.3f} ft")
        if not pos_match or not type_match:
            print(f"          Expected: {expected_type} at {expected_pos:.3f} ft - DIFF: {pos_diff:.3f} ft")
    else:
        print(f"Grid {name}: ERROR - {detail.get('error')}")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)

ok_count = sum(1 for r in results if r['status'] == 'OK')
mismatch_count = len(results) - ok_count

print(f"  Correct: {ok_count}")
print(f"  Mismatched: {mismatch_count}")

if mismatch_count > 0:
    print("\nMISMATCHED GRIDS:")
    for r in results:
        if r['status'] != 'OK':
            print(f"  Grid {r['name']}: {r['actual_type']} at {r['actual_pos']:.3f} vs expected {r['expected_type']} at {r['expected_pos']:.3f}")

# Print spacing verification
print("\n" + "=" * 70)
print("SPACING VERIFICATION:")
print("=" * 70)

# Sort results by name for grouping
vertical_grids = sorted([r for r in results if r['actual_type'] == 'vertical'], key=lambda x: x['actual_pos'])
horizontal_grids = sorted([r for r in results if r['actual_type'] == 'horizontal'], key=lambda x: -x['actual_pos'])

print("\nVertical grids (A-D, left to right):")
for i, g in enumerate(vertical_grids):
    print(f"  Grid {g['name']}: X = {g['actual_pos']:.3f} ft", end="")
    if i > 0:
        spacing = g['actual_pos'] - vertical_grids[i-1]['actual_pos']
        print(f"  (spacing from {vertical_grids[i-1]['name']}: {spacing:.3f} ft)")
    else:
        print()

print("\nHorizontal grids (1-5, top to bottom):")
for i, g in enumerate(horizontal_grids):
    print(f"  Grid {g['name']}: Y = {g['actual_pos']:.3f} ft", end="")
    if i > 0:
        spacing = horizontal_grids[i-1]['actual_pos'] - g['actual_pos']
        print(f"  (spacing from {horizontal_grids[i-1]['name']}: {spacing:.3f} ft)")
    else:
        print()

print("\nExpected spacing (from spec):")
print("  A-B: 7'-0\" (7.0 ft)")
print("  B-C: 17'-8\" (17.667 ft)")
print("  C-D: 13'-8\" (13.666 ft)")
print("  1-2: 12'-1\" (12.083 ft)")
print("  2-3: 15'-0\" (15.0 ft)")
print("  3-4: 8'-0\" (8.0 ft)")
print("  4-5: 15'-0\" (15.0 ft)")
