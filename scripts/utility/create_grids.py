import json
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def create_grid(name, start, end):
    handle = win32file.CreateFile(
        PIPE_NAME,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )

    request = {
        'method': 'createGrid',
        'params': {
            'name': name,
            'startPoint': start,
            'endPoint': end
        }
    }
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

# NEW ORIENTATION:
# Grids A-D: VERTICAL (running north-south, at different X positions)
# Grids 1-5: HORIZONTAL (running east-west, at different Y positions)

# From the original spec, swap the axes:
# Original horizontal_grids A-D had Y positions -> now become X positions for vertical grids
# Original vertical_grids 1-5 had X positions -> now become Y positions for horizontal grids

# VERTICAL grids A-D (left to right)
# Original spec: A=0, B=7, C=24.667, D=38.333 (these were Y, now X)
vertical_grids = [
    ('A', 0.0),       # Left edge
    ('B', 7.0),       # 7' from A
    ('C', 24.667),    # 24'-8" from origin
    ('D', 38.333),    # Right edge
]

# HORIZONTAL grids 1-5 (bottom to top)
# Original spec: 1=0, 2=12.083, 3=27.083, 4=35.083, 5=50.083 (these were X, now Y)
horizontal_grids = [
    ('1', 0.0),       # Bottom edge
    ('2', 12.083),    # 12'-1" from 1
    ('3', 27.083),    # 27'-1" from origin
    ('4', 35.083),    # 35'-1" from origin
    ('5', 50.083),    # Top edge
]

# Grid extents
x_min, x_max = -5.0, 45.0   # For horizontal grids
y_min, y_max = -5.0, 55.0   # For vertical grids

print('Creating VERTICAL grids A-D (left to right):')
print('=' * 50)
for name, x_pos in vertical_grids:
    result = create_grid(name, [x_pos, y_min, 0.0], [x_pos, y_max, 0.0])
    if result.get('success'):
        print(f'  Grid {name}: X = {x_pos} ft - Created (ID: {result.get("gridId")})')
    else:
        print(f'  Grid {name}: FAILED - {result.get("error")}')

print()
print('Creating HORIZONTAL grids 1-5 (bottom to top):')
print('=' * 50)
for name, y_pos in horizontal_grids:
    result = create_grid(name, [x_min, y_pos, 0.0], [x_max, y_pos, 0.0])
    if result.get('success'):
        print(f'  Grid {name}: Y = {y_pos} ft - Created (ID: {result.get("gridId")})')
    else:
        print(f'  Grid {name}: FAILED - {result.get("error")}')

print()
print('Done! Grid layout:')
print('''
      1 -------- 2 -------- 3 ---- 4 ---------- 5
      |          |          |      |            |
  A   +----------+----------+------+------------+  (Y=50.08)
      |          |          |      |            |
  B   +----------+----------+------+------------+  (Y=35.08)
      |          |          |      |            |
  C   +----------+----------+------+------------+  (Y=27.08)
      |          |          |      |            |
  D   +----------+----------+------+------------+  (Y=12.08)
      |          |          |      |            |
      +----------+----------+------+------------+  (Y=0)
      ^          ^          ^      ^            ^
    X=0        X=7       X=24.67  X=38.33
''')
