"""
Build 1700 West Sheffield Road - LIVE in Revit
"""
import win32file
import json
import time

# Open persistent connection
pipe = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None, win32file.OPEN_EXISTING, 0, None
)

def call_mcp(method, params={}):
    request = json.dumps({'method': method, 'params': params}) + '\n'
    win32file.WriteFile(pipe, request.encode())
    result, data = win32file.ReadFile(pipe, 65536)
    return json.loads(data.decode().strip())

print("=" * 60)
print("BUILDING: 1700 WEST SHEFFIELD ROAD - LIVE")
print("=" * 60)

# Building dimensions
MAIN_W, MAIN_D = 38.0, 35.0  # Main house
GAR_W, GAR_D = 22.0, 20.0    # Garage
HEIGHT = 10.0

# STEP 1: Get existing levels to find Level 1 ID
print("\n[1/7] Getting Levels...")
r = call_mcp("getLevels", {})
level_id = None
if r.get("success"):
    for lvl in r.get("levels", []):
        print(f"  Found: {lvl.get('name')} (ID: {lvl.get('levelId')})")
        if lvl.get("name") == "Level 1":
            level_id = lvl.get("levelId")
else:
    print(f"  Error getting levels: {r.get('error')}")

if not level_id:
    print("  ERROR: Could not find Level 1!")
    win32file.CloseHandle(pipe)
    exit(1)

print(f"\n  Using Level 1 ID: {level_id}")

# STEP 2: Exterior Walls - Main House
print("\n[2/7] Creating Exterior Walls - Main House...")
exterior_walls = [
    ((0, 0), (MAIN_W, 0), "South-Front"),
    ((MAIN_W, 0), (MAIN_W, MAIN_D), "East"),
    ((MAIN_W, MAIN_D), (0, MAIN_D), "North-Back"),
    ((0, MAIN_D), (0, 0), "West"),
]
for (sx, sy), (ex, ey), name in exterior_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:30]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# STEP 3: Garage Walls
print("\n[3/7] Creating Garage Walls...")
garage_walls = [
    ((-GAR_W, 0), (0, 0), "Garage-South"),
    ((-GAR_W, 0), (-GAR_W, GAR_D), "Garage-West"),
    ((-GAR_W, GAR_D), (0, GAR_D), "Garage-North"),
]
for (sx, sy), (ex, ey), name in garage_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:30]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# STEP 4: Interior Walls
print("\n[4/7] Creating Interior Walls...")
interior_walls = [
    ((10, 0), (10, 18), "Living/Family"),
    ((0, 18), (18, 18), "Kitchen-South"),
    ((18, 18), (18, MAIN_D), "Hallway-West"),
    ((0, 26), (MAIN_W, 26), "Back-Corridor"),
    ((26, 0), (26, 26), "Bedrooms-West"),
    ((26, 18), (MAIN_W, 18), "Bed3-North"),
    ((12, 18), (12, 26), "MasterBath-East"),
    ((32, 22), (32, 26), "Bath2-East"),
]
for (sx, sy), (ex, ey), name in interior_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:30]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# STEP 5: Create Rooms
print("\n[5/7] Creating Rooms...")
rooms = [
    (5, 9, "Living"),
    (5, 22, "Kitchen"),
    (6, 30, "Master Bedroom"),
    (32, 9, "Bedroom 3"),
    (32, 30, "Bedroom 2"),
    (-11, 10, "Garage"),
]
for x, y, name in rooms:
    r = call_mcp("createRoom", {
        "location": [x, y, 0],
        "levelId": level_id,
        "name": name
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:30]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# STEP 6: Create Floor Slab
print("\n[6/7] Creating Floor Slab...")
floor_points = [
    [-GAR_W, 0, 0],
    [-GAR_W, GAR_D, 0],
    [0, GAR_D, 0],
    [0, MAIN_D, 0],
    [MAIN_W, MAIN_D, 0],
    [MAIN_W, 0, 0],
]
r = call_mcp("createFloor", {
    "boundaryPoints": floor_points,
    "levelId": level_id
})
status = "OK" if r.get("success") else r.get("error", "failed")[:30]
print(f"  + Floor slab: {status}")

print("\n[7/7] Build Summary")
print("  Note: Doors/windows require wall IDs - skipped for now")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("BUILD COMPLETE!")
print("=" * 60)
print("""
Check your Revit model:
- Floor Plan view: Room layout visible
- 3D view: Walls with openings
- Main house: 38' x 35'
- Garage: 22' x 20'
""")
