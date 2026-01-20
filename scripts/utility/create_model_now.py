"""
CREATE MODEL NOW - Direct execution in blank Revit
"""
import win32file
import json
import time

pipe = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None, win32file.OPEN_EXISTING, 0, None
)

def call_mcp(method, params={}):
    request = json.dumps({'method': method, 'params': params}) + '\n'
    win32file.WriteFile(pipe, request.encode())
    chunks = []
    while True:
        result, data = win32file.ReadFile(pipe, 65536)
        chunks.append(data)
        combined = b''.join(chunks).decode()
        if combined.strip().endswith('}') or combined.strip().endswith(']'):
            break
        if len(data) < 1024:
            break
    return json.loads(b''.join(chunks).decode().strip())

print("=" * 70)
print("CREATING 1700 W SHEFFIELD RD MODEL")
print("=" * 70)

# Step 1: Get Level
print("\n[1] Getting Level...")
r = call_mcp("getLevels", {})
levels = r.get("levels", [])
print(f"Found {len(levels)} levels:")
for lvl in levels:
    print(f"  - {lvl.get('name')}: ID={lvl.get('levelId')}, Elev={lvl.get('elevation')}")

# Use Level 1 or first level at elevation 0
level_id = None
for lvl in levels:
    if "Level 1" in lvl.get("name", "") or lvl.get("elevation") == 0:
        level_id = lvl.get("levelId")
        print(f"\nUsing: {lvl.get('name')} (ID: {level_id})")
        break

if not level_id and levels:
    level_id = levels[0].get("levelId")
    print(f"\nUsing first level: ID={level_id}")

if not level_id:
    print("ERROR: No level found!")
    exit(1)

# Wall types - use Generic 8" for exterior, 4" for interior
EXT_WALL = 441451  # Generic - 8"
INT_WALL = 441519  # Interior - 4 1/2" Partition
HEIGHT = 10.0

# Step 2: Create Exterior Perimeter
print("\n[2] Creating Exterior Perimeter (8 walls)...")

exterior = [
    ((-24.73, 26.76), (30.19, 26.76), "North"),
    ((30.19, 26.76), (30.19, -19.49), "East"),
    ((30.19, -19.49), (10.94, -19.49), "South-East"),
    ((10.94, -19.49), (10.94, -13.16), "Entry-E"),
    ((10.94, -13.16), (1.52, -13.16), "Entry-Back"),
    ((1.52, -13.16), (1.52, -22.55), "Entry-W"),
    ((1.52, -22.55), (-24.73, -22.55), "South-West"),
    ((-24.73, -22.55), (-24.73, 26.76), "West"),
]

ext_ok = 0
for (sx, sy), (ex, ey), name in exterior:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": EXT_WALL
    })
    if r.get("success"):
        ext_ok += 1
        length = ((ex-sx)**2 + (ey-sy)**2)**0.5
        print(f"  {name}: {length:.1f}' - OK")
    else:
        print(f"  {name}: FAIL - {r.get('error', 'Unknown')}")
    time.sleep(0.05)

print(f"Exterior walls: {ext_ok}/8")

# Step 3: Create Interior Walls
print("\n[3] Creating Interior Partitions (31 walls)...")

interior = [
    ((-12.27, 26.76), (-12.27, 14.30)),
    ((-24.73, 14.30), (-8.27, 14.30)),
    ((0.06, 13.30), (0.06, 3.63)),
    ((-24.73, 6.13), (-16.27, 6.13)),
    ((-24.73, 3.80), (-12.27, 3.80)),
    ((-24.73, -8.54), (-1.94, -8.54)),
    ((0.06, 13.30), (30.19, 13.30)),
    ((22.06, 13.30), (22.06, 0.96)),
    ((30.19, 0.96), (11.18, 0.96)),
    ((12.73, 13.30), (12.73, 0.96)),
    ((-24.73, 11.96), (-16.27, 11.96)),
    ((-16.27, 14.30), (-16.27, 3.80)),
    ((-12.27, -8.54), (-12.27, 3.80)),
    ((-1.94, -12.92), (-1.94, 3.63)),
    ((-12.27, -0.70), (-1.94, -0.70)),
    ((-8.27, -8.54), (-8.27, -0.70)),
    ((-7.27, -22.49), (-7.27, -8.54)),
    ((12.73, 3.63), (-12.27, 3.63)),
    ((-8.27, 14.30), (-8.27, 3.63)),
    ((-8.27, 6.13), (0.06, 6.13)),
    ((-8.27, 11.96), (0.06, 11.96)),
    ((-3.94, 6.13), (-3.94, 3.63)),
    ((1.52, -12.92), (-7.27, -12.92)),
    ((11.18, -13.22), (11.18, 0.96)),
    ((30.19, 7.96), (22.06, 7.96)),
    ((12.73, 0.96), (12.73, 13.30)),
    ((1.52, -16.96), (-1.41, -16.96)),
    ((-8.27, 11.51), (-5.77, 11.51)),
    ((-5.77, 11.51), (-5.77, 11.96)),
    ((-24.73, 11.51), (-21.99, 11.51)),
    ((-21.99, 11.51), (-21.99, 11.96)),
]

int_ok = 0
for i, ((sx, sy), (ex, ey)) in enumerate(interior):
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": INT_WALL
    })
    if r.get("success"):
        int_ok += 1
    else:
        print(f"  Wall {i+1}: FAIL - {r.get('error', 'Unknown')[:50]}")
    time.sleep(0.03)

print(f"Interior walls: {int_ok}/31")

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70)
print("MODEL CREATION COMPLETE")
print("=" * 70)
print(f"""
Results:
  Exterior: {ext_ok}/8 walls
  Interior: {int_ok}/31 walls
  Total: {ext_ok + int_ok}/39 walls

Building: 54.92' x 49.31' with entry recess
""")
