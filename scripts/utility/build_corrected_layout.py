"""
Build Floor Plan - CORRECTED LAYOUT
Based on actual room arrangement in Floor plan.PNG

Key insight: Rooms are arranged in columns, not stacked by dimension strings
- Left column: Master Bath, Master Bedroom, Bedroom-2, Bedroom-3
- Center: Entry, W.I.C., Baths, Hall, Bedroom-4
- Right: Porch, Living, Kitchen, Family/Dining, Garage
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
print("BUILDING CORRECTED FLOOR PLAN LAYOUT")
print("=" * 70)

# Get Level 1
r = call_mcp("getLevels", {})
level_id = None
for lvl in r.get("levels", []):
    if lvl.get("name") == "Level 1":
        level_id = lvl.get("levelId")
print(f"Level 1 ID: {level_id}")

# Wall types
EXT_WALL = 441451  # 8"
INT_WALL = 441459  # 4"
HEIGHT = 10.0

# =============================================================================
# GRID BASED ON DIMENSION STRINGS
# =============================================================================

# Bottom dimension string (X-axis, left to right):
# 5'-4½" | 8'-10" | 7'-9½" | 5'-1½" | 8'-7" | 10'-0½" | 10'-0½"
X0 = 0
X1 = 5.375      # 5'-4½"
X2 = 14.208     # + 8'-10"
X3 = 22.0       # + 7'-9½"
X4 = 27.125     # + 5'-1½"
X5 = 35.708     # + 8'-7"
X6 = 45.75      # + 10'-0½"
X7 = 55.792     # + 10'-0½" (total width)

# Left dimension string (Y-axis, bottom to top):
# 7'-6½" | 13'-0½" | 22'-9½" | 6'-9½"
Y0 = 0
Y1 = 7.542      # 7'-6½"
Y2 = 20.584     # + 13'-0½"
Y3 = 43.376     # + 22'-9½"
Y4 = 50.168     # + 6'-9½" (total depth)

# Garage offset
GAR_Y = 3.0     # Garage starts 3' from bottom

print(f"\nBuilding: {X7:.1f}' wide × {Y4:.1f}' deep")
print(f"Grid: X = [{X0}, {X1}, {X2}, {X3}, {X4}, {X5}, {X6}, {X7}]")
print(f"Grid: Y = [{Y0}, {Y1}, {Y2}, {Y3}, {Y4}]")

# =============================================================================
# EXTERIOR WALLS
# =============================================================================
print("\n[1/4] Creating Exterior Walls (8\")...")

exterior = [
    # Main house perimeter (L-shaped)
    ((X0, Y0), (X0, Y4), "West"),
    ((X0, Y4), (X7, Y4), "North"),
    ((X7, Y4), (X7, GAR_Y + 19), "East-Upper"),  # Down to garage top
    ((X7, GAR_Y + 19), (X7, GAR_Y), "Garage-East"),
    ((X7, GAR_Y), (X5, GAR_Y), "Garage-South"),
    ((X5, GAR_Y), (X5, Y0), "East-Lower"),
    ((X5, Y0), (X0, Y0), "South"),
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

# =============================================================================
# INTERIOR WALLS - Based on actual floor plan layout
# =============================================================================
print("\n[2/4] Creating Interior Walls (4\")...")

interior = [
    # === Horizontal walls (running East-West) ===

    # Top bedroom row floor line
    ((X0, Y3), (X3, Y3), "Bed3-4-Floor"),

    # Bath row floor line
    ((X0, Y2 + 11), (X3, Y2 + 11), "Bath-Row-Floor"),  # Y = 31.5

    # Bedroom-2 floor line
    ((X0, Y2), (X3, Y2), "Bed2-Floor"),

    # Master bedroom top line
    ((X0, Y1), (X2, Y1), "Master-Top"),

    # Kitchen/utility horizontal
    ((X3, Y2 + 11), (X5, Y2 + 11), "Kitchen-Top"),
    ((X3, Y2), (X5, Y2), "Kitchen-Floor"),

    # Family/Dining floor
    ((X3, Y3), (X7, Y3), "Family-Floor"),

    # === Vertical walls (running North-South) ===

    # Left column divider
    ((X2, Y0), (X2, Y2), "MasterBath-East"),
    ((X2 - 4, Y2), (X2 - 4, Y3), "Bed2-East"),  # Bedroom-2 east wall

    # Bath dividers
    ((X1 + 2, Y2 + 11), (X1 + 2, Y3), "Bath2-East"),  # ~7.4'
    ((X2, Y2 + 11), (X2, Y3), "Hall1-East"),

    # Bedroom 3/4 divider
    ((X2 - 2, Y3), (X2 - 2, Y4), "Bed3-4-Divider"),  # ~12'

    # W.I.C. walls
    ((X2 - 4, Y2), (X2 - 4, Y2 + 4), "WIC-West"),
    ((X2, Y2), (X2, Y2 + 4), "WIC-East"),
    ((X2 - 4, Y2 + 4), (X2, Y2 + 4), "WIC-North"),

    # Living room walls
    ((X2, Y1), (X2, Y2 + 11), "Living-West"),
    ((X3, Y1), (X3, Y3), "Living-East"),

    # Kitchen/Laundry divider
    ((X5 - 5, Y2), (X5 - 5, Y2 + 8), "Laundry-West"),

    # Garage interior wall
    ((X5, GAR_Y + 19), (X7, GAR_Y + 19), "Garage-Top"),
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

# =============================================================================
# ROOMS - Placed at actual locations
# =============================================================================
print("\n[3/4] Creating Rooms...")

# Room positions based on floor plan layout
rooms = [
    # Left column (bottom to top)
    (X1, Y1/2, "Master Bath"),
    (X1, Y1 + 6.5, "Master Bedroom"),
    (5, Y2 + 5.5, "Bedroom-2"),
    (5, Y3 + 3.5, "Bedroom-3"),

    # Center column
    (X2 - 2, Y2 + 2, "W.I.C."),
    (X1 + 2, Y2 + 14, "Bath-2"),
    (X2 - 3, Y2 + 14, "Hall-1"),
    (X2 + 3, Y2 + 14, "Bath-3"),
    (X2 - 2 + 6, Y3 + 3.5, "Bedroom-4"),

    # Right side
    (X2 + 4, Y1 + 8, "Living"),
    (X3 + 6, Y2 + 5.5, "Kitchen"),
    (X5 - 3, Y2 + 4, "Laundry"),
    (X5 - 3, Y2 + 9, "Utility"),
    (X5 + 10, Y3 + 3.5, "Family/Dining"),

    # Bottom right
    (X4, Y0 + 2, "Porch"),
    (X6, GAR_Y + 9.5, "2-Car Garage"),
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

# =============================================================================
# FLOOR
# =============================================================================
print("\n[4/4] Creating Floor...")

floor_pts = [
    [X0, Y0, 0],
    [X5, Y0, 0],
    [X5, GAR_Y, 0],
    [X7, GAR_Y, 0],
    [X7, GAR_Y + 19, 0],
    [X7, Y4, 0],
    [X0, Y4, 0],
]
r = call_mcp("createFloor", {"boundaryPoints": floor_pts, "levelId": level_id})
print(f"  Floor: {'OK' if r.get('success') else str(r.get('error', '?'))[:20]}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("CORRECTED FLOOR PLAN COMPLETE!")
print("=" * 70)
print(f"""
Building: {X7:.1f}' × {Y4:.1f}'
Exterior walls: 8"
Interior walls: 4"

Layout based on actual floor plan arrangement.
Check Revit model for accuracy.
""")
