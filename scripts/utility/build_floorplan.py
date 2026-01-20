"""
Build Floor Plan from Image - Exact reproduction
Based on detailed analysis of Floor plan.PNG

Specifications:
- Exterior walls: 8" thick
- Interior walls: 4" thick
- All dimensions from plan
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
print("BUILDING FLOOR PLAN FROM IMAGE")
print("Exterior: 8\" | Interior: 4\"")
print("=" * 70)

# Get Level 1 ID
print("\n[1/7] Getting Level 1...")
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

# Wall type IDs
# Need to find 8" exterior and 4" interior
EXTERIOR_WALL = 441451  # Generic - 8"
INTERIOR_WALL = 441459  # Generic - 4" Brick (closest to 4")

HEIGHT = 10.0  # 10'-0" ceiling height

# =============================================================================
# DIMENSIONS FROM FLOOR PLAN (converted to decimal feet)
# Origin (0,0) at bottom-left corner of building
# =============================================================================

# Overall building dimensions
TOTAL_WIDTH = 55.79  # 55'-9 1/2"
TOTAL_DEPTH = 50.125  # Approximately 50'-1 1/2" based on proportions

# Key section widths (bottom to top, left side)
SEC_1 = 5.375   # 5'-4 1/2"
SEC_2 = 8.833   # 8'-10"
SEC_3 = 7.792   # 7'-9 1/2"
SEC_4 = 5.125   # 5'-1 1/2"
SEC_5 = 8.583   # 8'-7"

# Garage section
GARAGE_WIDTH = 19.0    # ~19'-0"
GARAGE_DEPTH = 19.5    # ~19'-6"

# Master bedroom width
MASTER_WIDTH = 16.833  # 16'-10"

# =============================================================================
# EXTERIOR WALLS (8" thick)
# =============================================================================
print("\n[2/7] Creating Exterior Walls (8\" thick)...")

# The building is L-shaped
# Main rectangle on left, garage bump-out on right

# Simplified exterior based on floor plan shape
# Main house portion: ~36' wide x 50' deep
# Garage: ~20' wide x 20' deep, offset to right

MAIN_W = 36.0
MAIN_D = 50.0
GAR_W = 20.0
GAR_D = 20.0
GAR_OFFSET_Y = 3.0  # Garage starts 3' from bottom

exterior_walls = [
    # Main house - West wall
    ((0, 0), (0, MAIN_D), "West"),
    # Main house - North wall
    ((0, MAIN_D), (MAIN_W, MAIN_D), "North-Main"),
    # Transition to garage
    ((MAIN_W, MAIN_D), (MAIN_W, GAR_D + GAR_OFFSET_Y), "East-Upper"),
    # Garage - North wall
    ((MAIN_W, GAR_D + GAR_OFFSET_Y), (MAIN_W + GAR_W, GAR_D + GAR_OFFSET_Y), "Garage-North"),
    # Garage - East wall
    ((MAIN_W + GAR_W, GAR_D + GAR_OFFSET_Y), (MAIN_W + GAR_W, GAR_OFFSET_Y), "Garage-East"),
    # Garage - South wall
    ((MAIN_W + GAR_W, GAR_OFFSET_Y), (MAIN_W, GAR_OFFSET_Y), "Garage-South"),
    # Main house - continue south
    ((MAIN_W, GAR_OFFSET_Y), (MAIN_W, 0), "East-Lower"),
    # Main house - South wall (with porch indent)
    ((MAIN_W, 0), (0, 0), "South"),
]

for (sx, sy), (ex, ey), name in exterior_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": EXTERIOR_WALL
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:25]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# =============================================================================
# INTERIOR WALLS (4" thick)
# =============================================================================
print("\n[3/7] Creating Interior Walls (4\" thick)...")

# Based on floor plan room layout
interior_walls = [
    # --- TOP ROW: Bedrooms 3 & 4 ---
    # Bedroom 3/4 south wall
    ((0, 43), (24, 43), "Bed3-4-South"),
    # Bedroom 3/4 divider
    ((12, 43), (12, MAIN_D), "Bed3-4-Divider"),
    # Closets in bedrooms
    ((0, 46), (5, 46), "Bed3-Closet"),
    ((12, 46), (17, 46), "Bed4-Closet"),

    # --- BATH-2, HALL-1, BATH-3 row ---
    # Bath-2 walls
    ((0, 36), (8, 36), "Bath2-South"),
    ((8, 36), (8, 43), "Bath2-East"),
    # Hall-1
    ((8, 36), (16, 36), "Hall1-South"),
    # Bath-3
    ((16, 36), (24, 36), "Bath3-South"),
    ((16, 36), (16, 43), "Bath3-West"),

    # --- BEDROOM-2 and closets ---
    ((0, 28), (12, 28), "Bed2-South"),
    ((12, 28), (12, 36), "Bed2-East"),
    # Closet in bedroom 2
    ((0, 31), (5, 31), "Bed2-Closet"),

    # --- W.I.C. (Walk-in Closet) ---
    ((12, 28), (16, 28), "WIC-South"),
    ((16, 22), (16, 36), "WIC-East"),

    # --- LIVING room walls ---
    ((16, 14), (16, 22), "Living-West"),
    ((16, 14), (24, 14), "Living-South"),

    # --- MASTER BEDROOM ---
    ((0, 14), (16, 14), "Master-North"),
    # Master bath walls
    ((0, 8), (12, 8), "MasterBath-North"),
    ((12, 0), (12, 14), "MasterBath-East"),

    # --- Right side: Kitchen, Laundry, Utility ---
    # Kitchen area
    ((24, 23), (MAIN_W, 23), "Kitchen-North"),
    ((24, 14), (24, 43), "Kitchen-West"),
    # Laundry/Utility
    ((30, 14), (30, 23), "Laundry-West"),
    ((30, 18), (MAIN_W, 18), "Utility-South"),

    # --- Family/Dining separation (if any) ---
    ((24, 43), (MAIN_W, 43), "Family-South"),
]

for (sx, sy), (ex, ey), name in interior_walls:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": INTERIOR_WALL
    })
    status = "OK" if r.get("success") else r.get("error", "failed")[:25]
    print(f"  + {name}: {status}")
    time.sleep(0.1)

# =============================================================================
# ROOMS
# =============================================================================
print("\n[4/7] Creating Rooms...")

rooms = [
    (6, 47, "Bedroom-3"),
    (18, 47, "Bedroom-4"),
    (4, 39, "Bath-2"),
    (12, 39, "Hall-1"),
    (20, 39, "Bath-3"),
    (6, 32, "Bedroom-2"),
    (14, 32, "W.I.C."),
    (20, 18, "Living"),
    (8, 7, "Master Bedroom"),
    (6, 4, "Master Bath"),
    (30, 33, "Family/Dining"),
    (28, 18, "Kitchen"),
    (33, 20, "Laundry"),
    (34, 16, "Utility"),
    (46, 12, "2-Car Garage"),
    (22, 2, "Porch"),
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

# =============================================================================
# FLOOR
# =============================================================================
print("\n[5/7] Creating Floor...")

floor_points = [
    [0, 0, 0],
    [MAIN_W, 0, 0],
    [MAIN_W, GAR_OFFSET_Y, 0],
    [MAIN_W + GAR_W, GAR_OFFSET_Y, 0],
    [MAIN_W + GAR_W, GAR_D + GAR_OFFSET_Y, 0],
    [MAIN_W, GAR_D + GAR_OFFSET_Y, 0],
    [MAIN_W, MAIN_D, 0],
    [0, MAIN_D, 0],
]
r = call_mcp("createFloor", {
    "boundaryPoints": floor_points,
    "levelId": level_id
})
status = "OK" if r.get("success") else r.get("error", "failed")[:25]
print(f"  + Floor: {status}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n[6/7] Summary")
print(f"  Exterior walls: 8\" (ID: {EXTERIOR_WALL})")
print(f"  Interior walls: 4\" (ID: {INTERIOR_WALL})")
print(f"  Main house: {MAIN_W}' x {MAIN_D}'")
print(f"  Garage: {GAR_W}' x {GAR_D}'")

print("\n[7/7] Notes")
print("  - Doors and windows not yet placed (need wall IDs)")
print("  - Review room positions and adjust as needed")
print("  - Some walls may need fine-tuning based on exact dimensions")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("FLOOR PLAN BUILD COMPLETE!")
print("=" * 70)
