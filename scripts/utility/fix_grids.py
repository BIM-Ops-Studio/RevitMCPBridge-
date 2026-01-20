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

# Step 1: Get current grids
print("Getting current grids...")
response = call_mcp('getGrids', {})
grids = response.get('grids', [])
print(f"Found {len(grids)} grids")

# Step 2: Find and delete horizontal grids 1-5
grid_ids_to_delete = []
for g in grids:
    if g['name'] in ['1', '2', '3', '4', '5']:
        grid_ids_to_delete.append(g['gridId'])
        print(f"  Will delete Grid {g['name']} (ID: {g['gridId']})")

if grid_ids_to_delete:
    print("\nDeleting grids 1-5...")
    result = call_mcp('deleteElements', {'elementIds': grid_ids_to_delete})
    print(f"Delete result: {result.get('success', False)}")

# Step 3: Recreate horizontal grids with REVERSED order
# Grid 1 at TOP (Y=50.083), Grid 5 at BOTTOM (Y=0)
print("\nCreating horizontal grids with correct order:")
print("  Grid 1 at TOP, Grid 5 at BOTTOM")
print("=" * 50)

# CORRECTED: Grid 1 at top (highest Y), Grid 5 at bottom (lowest Y)
horizontal_grids = [
    ('1', 50.083),    # TOP - was Grid 5's position
    ('2', 35.083),    # was Grid 4's position
    ('3', 27.083),    # stays in middle
    ('4', 12.083),    # was Grid 2's position
    ('5', 0.0),       # BOTTOM - was Grid 1's position
]

x_min, x_max = -5.0, 45.0

for name, y_pos in horizontal_grids:
    result = create_grid(name, [x_min, y_pos, 0.0], [x_max, y_pos, 0.0])
    if result.get('success'):
        print(f"  Grid {name}: Y = {y_pos} ft - Created (ID: {result.get('gridId')})")
    else:
        print(f"  Grid {name}: FAILED - {result.get('error')}")

print("\nDone! Grid layout:")
print("""
  Grid 1 (TOP)    --------------------------------  Y = 50.08 ft

  Grid 2          --------------------------------  Y = 35.08 ft

  Grid 3          --------------------------------  Y = 27.08 ft

  Grid 4          --------------------------------  Y = 12.08 ft

  Grid 5 (BOTTOM) --------------------------------  Y = 0.0 ft
       |     |          |        |
       A     B          C        D
     X=0   X=7       X=24.67   X=38.33
""")
