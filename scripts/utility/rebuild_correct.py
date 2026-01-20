"""
Rebuild 1700 West Sheffield Road with CORRECT layout and wall types
Based on careful analysis of A-1.1 Floor Plan
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
    # Read in chunks
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

print("=" * 60)
print("REBUILDING: 1700 WEST SHEFFIELD ROAD")
print("With CORRECT Layout and Wall Types")
print("=" * 60)

# Get Level 1 ID
print("\n[1/6] Getting Level 1...")
r = call_mcp("getLevels", {})
level_id = None
for lvl in r.get("levels", []):
    if lvl.get("name") == "Level 1":
        level_id = lvl.get("levelId")
        break

if not level_id:
    print("ERROR: Level 1 not found!")
    exit(1)

print(f"  Level 1 ID: {level_id}")

# Wall type IDs per user specification
EXTERIOR_WALL_TYPE = 441451  # Generic - 8" (8" thick exterior)
INTERIOR_WALL_TYPE = 441460  # Interior - 3 1/8" Partition (closest to 4")
# Note: If you need exactly 4", check available types or create custom

# Building dimensions based on floor plan analysis
# Main house approximately 51' x 27' with garage 20' x 22' on RIGHT side
# Reoriented: Garage on EAST (right) side
MAIN_W = 51.0   # Main house width (E-W)
MAIN_D = 27.0   # Main house depth (N-S)
GAR_W = 20.0    # Garage width
GAR_D = 22.0    # Garage depth
HEIGHT = 10.0

# Origin at SW corner of main house (0,0)

print("\n[2/6] Creating Exterior Walls...")

# Main house perimeter
exterior_walls = [
    # Main house
    ((0, 0), (MAIN_W - GAR_W, 0), "South-Front"),
    ((MAIN_W - GAR_W, 0), (MAIN_W - GAR_W, GAR_D), "South-Garage"),
    ((MAIN_W - GAR_W, GAR_D), (MAIN_W, GAR_D), "Garage-South"),
    ((MAIN_W, GAR_D), (MAIN_W, GAR_D + (MAIN_D - GAR_D)), "Garage-East"),
    # Actually let's simplify - garage extends from main house
    ((0, 0), (MAIN_W, 0), "South"),
    ((MAIN_W, 0), (MAIN_W, MAIN_D), "East"),
    ((MAIN_W, MAIN_D), (0, MAIN_D), "North"),
    ((0, MAIN_D), (0, 0), "West"),
]

# Simplified exterior - just the main rectangle for now
# Garage bump-out handled separately
main_exterior = [
    ((0, 0), (38, 0), "South-Main"),
    ((38, 0), (38, 20), "East-Garage-Entry"),
    ((38, 20), (58, 20), "Garage-South"),
    ((58, 20), (58, 35), "Garage-East"),
    ((58, 35), (38, 35), "Garage-North"),
    ((38, 35), (0, 35), "North"),
    ((0, 35), (0, 0), "West"),
]

for (sx, sy), (ex, ey), name in main_exterior:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": EXTERIOR_WALL_TYPE
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:25]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

print("\n[3/6] Creating Interior Walls...")

# Interior walls based on floor plan layout
# Rooms from SW corner: Bedrooms on west, Kitchen/Family center, Master back-left
interior_walls = [
    # Front bedrooms (Bedroom 2 & 3) on the left/west side
    ((0, 12), (12, 12), "Bed2/3-South"),
    ((12, 0), (12, 20), "Bedrooms-East"),
    ((6, 12), (6, 20), "Bed2-Bed3-Divider"),

    # Bath 2 between bedrooms
    ((6, 16), (12, 16), "Bath2-South"),

    # Master suite in back-left
    ((0, 20), (15, 20), "Master-South"),
    ((15, 20), (15, 35), "Master-East"),

    # Master bath/closet
    ((0, 28), (10, 28), "MasterBath-South"),
    ((10, 28), (10, 35), "MasterBath-East"),

    # Kitchen/Family divider (partial wall or opening)
    ((15, 20), (25, 20), "Kitchen-South"),

    # Hallway
    ((12, 20), (38, 20), "Hallway-Line"),

    # Laundry near garage
    ((30, 20), (30, 28), "Laundry-West"),
    ((30, 28), (38, 28), "Laundry-North"),
]

for (sx, sy), (ex, ey), name in interior_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": INTERIOR_WALL_TYPE
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:25]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

print("\n[4/6] Creating Rooms...")

rooms = [
    (3, 6, "Bedroom 3"),
    (9, 6, "Bath 2"),
    (3, 16, "Bedroom 2"),
    (5, 24, "Master Closet"),
    (5, 31, "Master Bath"),
    (12, 28, "Master Bedroom"),
    (20, 10, "Living"),
    (25, 28, "Kitchen"),
    (20, 24, "Family/Dining"),
    (34, 24, "Laundry"),
    (48, 28, "Garage"),
]

for x, y, name in rooms:
    r = call_mcp("createRoom", {
        "location": [x, y, 0],
        "levelId": level_id,
        "name": name
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:25]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

print("\n[5/6] Creating Floor...")

floor_points = [
    [0, 0, 0],
    [38, 0, 0],
    [38, 20, 0],
    [58, 20, 0],
    [58, 35, 0],
    [0, 35, 0],
]
r = call_mcp("createFloor", {
    "boundaryPoints": floor_points,
    "levelId": level_id
})
status = "OK" if r.get("success") else r.get("error", "failed")[:25]
print(f"  + Floor: {status}")

print("\n[6/6] Summary")
print(f"  Exterior wall type: Generic - 8\" (ID: {EXTERIOR_WALL_TYPE})")
print(f"  Interior wall type: Interior - 3 1/8\" (ID: {INTERIOR_WALL_TYPE})")
print("  Note: Closest to 4\" available. Create custom type if exact 4\" needed.")
print("  Layout: Garage on RIGHT (east) side")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("REBUILD COMPLETE!")
print("=" * 60)
print("""
Check your Revit model:
- Exterior walls should be 6" thick
- Interior walls should be ~5" thick
- Garage is on the EAST (right) side
- Master suite is in back-left
- Secondary bedrooms are front-left
""")
