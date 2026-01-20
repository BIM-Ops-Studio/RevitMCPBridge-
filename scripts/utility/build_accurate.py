"""
Build Floor Plan - ACCURATE version based on dimension strings
Total width: 55'-9 1/2" (55.79')
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
print("BUILDING ACCURATE FLOOR PLAN")
print("=" * 70)

# Get Level 1
r = call_mcp("getLevels", {})
level_id = None
for lvl in r.get("levels", []):
    if lvl.get("name") == "Level 1":
        level_id = lvl.get("levelId")
print(f"Level 1 ID: {level_id}")

# Wall types: 8" exterior, 4" interior
EXT_WALL = 441451  # Generic - 8"
INT_WALL = 441459  # Generic - 4" Brick
HEIGHT = 10.0

# =============================================================================
# DIMENSIONS FROM FLOOR PLAN (all in decimal feet)
# Using bottom-left corner of building as origin (0, 0)
# X = right (East), Y = up (North)
# =============================================================================

# Bottom dimension string (left to right):
# 5'-4 1/2" | 8'-10" | 7'-9 1/2" | 5'-1 1/2" | 8'-7" | 10'-0 1/2" | 10'-0 1/2"
X1 = 5.375      # First section
X2 = X1 + 8.833  # 14.208
X3 = X2 + 7.792  # 22.0
X4 = X3 + 5.125  # 27.125
X5 = X4 + 8.583  # 35.708  (end of main house)
X6 = X5 + 10.042 # 45.75
X7 = X6 + 10.042 # 55.792  (total width)

# Vertical dimensions (approximate based on proportions)
# Total depth approximately 50'
Y_TOTAL = 50.0

# Key vertical breakpoints (from bottom):
Y1 = 7.5    # Top of master bath / porch area
Y2 = 14.0   # Top of master bedroom
Y3 = 28.0   # Top of bedroom-2 / living area
Y4 = 36.0   # Top of bath row
Y5 = 43.0   # Top of closets row
Y6 = Y_TOTAL  # Top of building (50')

# Garage dimensions
GAR_Y_START = 3.0   # Garage starts 3' up from bottom
GAR_Y_END = 23.0    # Garage height ~20'

print("\n[1/5] Creating Exterior Walls (8\")...")

# Exterior perimeter (clockwise from bottom-left)
exterior = [
    # West wall (full height)
    ((0, 0), (0, Y6), "West"),
    # North wall (full width)
    ((0, Y6), (X7, Y6), "North"),
    # East wall - upper portion
    ((X7, Y6), (X7, GAR_Y_END), "East-Upper"),
    # East wall - garage
    ((X7, GAR_Y_END), (X7, GAR_Y_START), "East-Garage"),
    # Garage south wall
    ((X7, GAR_Y_START), (X5, GAR_Y_START), "Garage-South"),
    # Step back to main house
    ((X5, GAR_Y_START), (X5, 0), "Main-East"),
    # South wall
    ((X5, 0), (0, 0), "South"),
]

for (sx, sy), (ex, ey), name in exterior:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": EXT_WALL
    })
    status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
    print(f"  {name}: {status}")
    time.sleep(0.1)

print("\n[2/5] Creating Interior Walls (4\")...")

# Interior walls based on room layout
interior = [
    # === TOP ROW: Bedrooms 3 & 4 ===
    # South wall of bedrooms 3 & 4
    ((0, Y5), (X3, Y5), "Bed3-4-South"),
    # Divider between bedroom 3 and 4
    ((X1 + 6, Y5), (X1 + 6, Y6), "Bed3-4-Divider"),

    # === BATH ROW ===
    # South wall of bath row
    ((0, Y4), (X3, Y4), "BathRow-South"),
    # Bath-2 east wall
    ((8, Y4), (8, Y5), "Bath2-East"),
    # Bath-3 west wall
    ((16, Y4), (16, Y5), "Bath3-West"),

    # === BEDROOM-2 / WIC / LIVING row ===
    # Bedroom-2 south wall
    ((0, Y3), (12, Y3), "Bed2-South"),
    # Bedroom-2 east wall
    ((12, Y3), (12, Y4), "Bed2-East"),
    # W.I.C. south wall
    ((12, Y3), (16, Y3), "WIC-South"),
    # W.I.C. east wall continues down
    ((16, Y3), (16, Y2), "WIC-Living-Divider"),

    # === MASTER suite ===
    # Master bedroom north wall
    ((0, Y2), (16, Y2), "Master-North"),
    # Master bath north wall
    ((0, Y1), (12, Y1), "MasterBath-North"),
    # Master bath east wall
    ((12, Y1), (12, Y2), "MasterBath-East"),

    # === Right side: Kitchen, Utility, Laundry ===
    # Main divider between living/family and kitchen area
    ((X3, Y4), (X3, Y2), "Kitchen-West"),
    # Kitchen south wall
    ((X3, Y2 + 8), (X5, Y2 + 8), "Kitchen-South"),
    # Utility/Laundry divider
    ((X5 - 6, Y2), (X5 - 6, Y2 + 8), "Laundry-West"),

    # === Family/Dining south wall ===
    ((X3, Y5), (X7, Y5), "Family-South"),
]

for (sx, sy), (ex, ey), name in interior:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": INT_WALL
    })
    status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
    print(f"  {name}: {status}")
    time.sleep(0.1)

print("\n[3/5] Creating Rooms...")

rooms = [
    (3, Y5 + 3, "Bedroom-3"),
    (X1 + 9, Y5 + 3, "Bedroom-4"),
    (4, Y4 + 3, "Bath-2"),
    (12, Y4 + 3, "Hall-1"),
    (20, Y4 + 3, "Bath-3"),
    (6, Y3 + 4, "Bedroom-2"),
    (14, Y3 + 4, "W.I.C."),
    (20, Y2 + 6, "Living"),
    (8, Y1 + 3, "Master Bedroom"),
    (6, 4, "Master Bath"),
    (40, Y5 + 3, "Family/Dining"),
    (28, Y2 + 12, "Kitchen"),
    (32, Y2 + 4, "Laundry"),
    (50, GAR_Y_START + 8, "2-Car Garage"),
]

for x, y, name in rooms:
    r = call_mcp("createRoom", {
        "location": [x, y, 0],
        "levelId": level_id,
        "name": name
    })
    status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
    print(f"  {name}: {status}")
    time.sleep(0.1)

print("\n[4/5] Creating Floor...")

floor_pts = [
    [0, 0, 0],
    [X5, 0, 0],
    [X5, GAR_Y_START, 0],
    [X7, GAR_Y_START, 0],
    [X7, Y6, 0],
    [0, Y6, 0],
]
r = call_mcp("createFloor", {"boundaryPoints": floor_pts, "levelId": level_id})
print(f"  Floor: {'OK' if r.get('success') else r.get('error', '?')[:20]}")

print("\n[5/5] Summary")
print(f"  Total width: {X7:.1f}' (55'-9 1/2\")")
print(f"  Total depth: {Y6:.1f}'")
print(f"  Exterior: 8\" walls")
print(f"  Interior: 4\" walls")

win32file.CloseHandle(pipe)
print("\n" + "=" * 70)
print("BUILD COMPLETE - Check Revit model")
print("=" * 70)
