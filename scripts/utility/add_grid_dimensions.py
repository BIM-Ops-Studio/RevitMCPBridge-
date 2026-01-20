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

# Get the grid IDs
print("Getting grid IDs...")
response = call_mcp('getGrids', {})
grids = response.get('grids', [])

grid_map = {g['name']: g['gridId'] for g in grids}
print(f"Found grids: {list(grid_map.keys())}")

# Try batchDimensionGrids
print("\nTrying batchDimensionGrids...")
result = call_mcp('batchDimensionGrids', {})
print(f"Result: {json.dumps(result, indent=2)}")

# Also try createLinearDimension for more control
# Get vertical grid IDs (A, B, C, D)
vertical_ids = [grid_map.get(name) for name in ['A', 'B', 'C', 'D'] if grid_map.get(name)]
horizontal_ids = [grid_map.get(name) for name in ['1', '2', '3', '4', '5'] if grid_map.get(name)]

print(f"\nVertical grid IDs (A-D): {vertical_ids}")
print(f"Horizontal grid IDs (1-5): {horizontal_ids}")

# Try createLinearDimension with grid references
if vertical_ids:
    print("\nTrying createLinearDimension for vertical grids...")
    result = call_mcp('createLinearDimension', {
        'referenceIds': vertical_ids,
        'dimensionLine': [-3.0, 25.0, 0.0]  # Position of dimension line
    })
    print(f"Result: {json.dumps(result, indent=2)}")

if horizontal_ids:
    print("\nTrying createLinearDimension for horizontal grids...")
    result = call_mcp('createLinearDimension', {
        'referenceIds': horizontal_ids,
        'dimensionLine': [20.0, -3.0, 0.0]  # Position of dimension line
    })
    print(f"Result: {json.dumps(result, indent=2)}")

print("\nGrid layout with correct dimensions:")
print("=" * 60)
print("HORIZONTAL GRIDS (top to bottom):")
print("  Grid 1: Y = 50'-1\" (top)")
print("  Grid 2: Y = 38'-0\" (12'-1\" below Grid 1)")
print("  Grid 3: Y = 23'-0\" (15'-0\" below Grid 2)")
print("  Grid 4: Y = 15'-0\" (8'-0\" below Grid 3)")
print("  Grid 5: Y = 0'-0\" (15'-0\" below Grid 4)")
print("")
print("VERTICAL GRIDS (left to right):")
print("  Grid A: X = 0'-0\" (left)")
print("  Grid B: X = 7'-0\" (7'-0\" from A)")
print("  Grid C: X = 24'-8\" (17'-8\" from A)")
print("  Grid D: X = 38'-4\" (38'-4\" from A)")
