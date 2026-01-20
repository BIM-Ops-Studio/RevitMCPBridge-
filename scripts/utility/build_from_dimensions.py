"""
Build Floor Plan from Extracted Room Dimensions
All dimensions in feet (converted from feet-inches)

Exterior walls: 8"
Interior walls: 4"
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
print("BUILDING FLOOR PLAN FROM EXTRACTED DIMENSIONS")
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
# ROOM DIMENSIONS (converted to decimal feet)
# =============================================================================

# Bedrooms
BED3_W, BED3_L = 11.833, 11.833      # 11'-10" × 11'-10"
BED4_W, BED4_L = 11.958, 11.833      # 11'-11½" × 11'-10"
BED2_W, BED2_L = 11.833, 11.958      # 11'-10" × 11'-11½"
MASTER_W, MASTER_L = 16.833, 13.042  # 16'-10" × 13'-0½"

# Bathrooms
BATH2_W, BATH2_L = 7.833, 5.458      # 7'-10" × 5'-5½"
BATH3_W, BATH3_L = 7.958, 5.458      # 7'-11½" × 5'-5½"
MBATH_W, MBATH_L = 7.792, 7.542      # 7'-9½" × 7'-6½"

# Living spaces
LIVING_W, LIVING_L = 7.833, 15.875   # 7'-10" × 15'-10½"
FAMILY_W, FAMILY_L = 29.5, 12.75     # 29'-6" × 12'-9"
KITCHEN_W, KITCHEN_L = 11.042, 11.958  # 11'-0½" × 11'-11½"

# Utility
HALL1_W, HALL1_L = 10.958, 5.458     # 10'-11½" × 5'-5½"
LAUNDRY_W, LAUNDRY_L = 7.5, 7.0      # 7'-6" × 7'-0"
PORCH_W, PORCH_L = 12.75, 3.083      # 12'-9" × 3'-1"
GARAGE_W, GARAGE_L = 18.417, 19.0    # 18'-5" × 19'-0"

# W.I.C.
WIC_W, WIC_L = 3.625, 3.958          # 3'-7½" × 3'-11½"

# =============================================================================
# ROOM POSITIONS (X, Y of bottom-left corner of each room)
# Origin (0,0) at bottom-left of building
# =============================================================================

# Y coordinates (bottom to top)
Y0 = 0                               # Bottom of building
Y1 = MBATH_L                         # 7.542 - Top of master bath
Y2 = Y1 + MASTER_L                   # 20.584 - Top of master bedroom
Y3 = Y2 + BED2_L                     # 32.542 - Top of bedroom-2
Y4 = Y3 + BATH2_L                    # 38.0 - Top of bath row
Y5 = Y4 + BED3_L                     # 49.833 - Top of building

# X coordinates (left to right)
X0 = 0                               # Left edge
X1 = BED3_W                          # 11.833 - Right of bedroom-3
X2 = X1 + BED4_W                     # 23.791 - Right of bedroom-4
X3 = X2 + FAMILY_W                   # 53.291 - Right edge (main)

# Garage position
GARAGE_X = X3 - GARAGE_W             # Garage on right side
GARAGE_Y = 3.0                       # Offset from bottom

print(f"\nBuilding size: {X3:.1f}' wide × {Y5:.1f}' tall")
print(f"Plus garage: {GARAGE_W:.1f}' × {GARAGE_L:.1f}'")

# =============================================================================
# EXTERIOR WALLS
# =============================================================================
print("\n[1/4] Creating Exterior Walls (8\")...")

exterior = [
    # Main house perimeter
    ((X0, Y0), (X0, Y5), "West"),
    ((X0, Y5), (X3, Y5), "North"),
    ((X3, Y5), (X3, GARAGE_Y + GARAGE_L), "East-Upper"),
    ((X3, GARAGE_Y + GARAGE_L), (X3 + 3, GARAGE_Y + GARAGE_L), "Garage-North"),
    ((X3 + 3, GARAGE_Y + GARAGE_L), (X3 + 3, GARAGE_Y), "Garage-East"),
    ((X3 + 3, GARAGE_Y), (X3, GARAGE_Y), "Garage-South"),
    ((X3, GARAGE_Y), (X3, Y0), "East-Lower"),
    ((X3, Y0), (X0, Y0), "South"),
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
# INTERIOR WALLS
# =============================================================================
print("\n[2/4] Creating Interior Walls (4\")...")

interior = [
    # --- Bedroom row (top) ---
    ((X0, Y4), (X2, Y4), "Bed3-4-South"),
    ((X1, Y4), (X1, Y5), "Bed3-4-Divider"),

    # --- Bath row ---
    ((X0, Y3), (X2, Y3), "BathRow-South"),
    ((BATH2_W, Y3), (BATH2_W, Y4), "Bath2-East"),
    ((BATH2_W + HALL1_W, Y3), (BATH2_W + HALL1_W, Y4), "Bath3-West"),

    # --- Bedroom-2 / W.I.C. row ---
    ((X0, Y2), (X1 + WIC_W, Y2), "Bed2-WIC-South"),
    ((X1, Y2), (X1, Y3), "Bed2-East"),
    ((X1 + WIC_W, Y2), (X1 + WIC_W, Y3), "WIC-East"),

    # --- Master suite ---
    ((X0, Y1), (MASTER_W, Y1), "Master-North"),
    ((MBATH_W, Y0), (MBATH_W, Y1), "MasterBath-East"),

    # --- Living / Kitchen divider ---
    ((X1 + WIC_W, Y1), (X1 + WIC_W, Y3), "Living-West"),

    # --- Right side rooms ---
    ((X2, Y3), (X2, Y1), "Kitchen-West"),
    ((X2, Y1 + KITCHEN_L), (X3, Y1 + KITCHEN_L), "Kitchen-North"),
    ((X3 - LAUNDRY_W, Y1), (X3 - LAUNDRY_W, Y1 + LAUNDRY_L), "Laundry-West"),

    # --- Family/Dining south ---
    ((X2, Y4), (X3, Y4), "Family-South"),
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
# ROOMS
# =============================================================================
print("\n[3/4] Creating Rooms...")

rooms = [
    (BED3_W/2, Y4 + BED3_L/2, "Bedroom-3"),
    (X1 + BED4_W/2, Y4 + BED4_L/2, "Bedroom-4"),
    (BATH2_W/2, Y3 + BATH2_L/2, "Bath-2"),
    (BATH2_W + HALL1_W/2, Y3 + HALL1_L/2, "Hall-1"),
    (BATH2_W + HALL1_W + BATH3_W/2, Y3 + BATH3_L/2, "Bath-3"),
    (BED2_W/2, Y2 + BED2_L/2, "Bedroom-2"),
    (X1 + WIC_W/2, Y2 + WIC_L/2, "W.I.C."),
    (X1 + WIC_W + LIVING_W/2, Y1 + LIVING_L/2, "Living"),
    (MASTER_W/2, Y1 + MASTER_L/2, "Master Bedroom"),
    (MBATH_W/2, MBATH_L/2, "Master Bath"),
    (X2 + FAMILY_W/2, Y4 + FAMILY_L/2, "Family/Dining"),
    (X2 + KITCHEN_W/2, Y1 + KITCHEN_L/2, "Kitchen"),
    (X3 - LAUNDRY_W/2, Y1 + LAUNDRY_L/2, "Laundry"),
    (X3 + 1.5, GARAGE_Y + GARAGE_L/2, "2-Car Garage"),
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
    [X3, Y0, 0],
    [X3, GARAGE_Y, 0],
    [X3 + 3, GARAGE_Y, 0],
    [X3 + 3, GARAGE_Y + GARAGE_L, 0],
    [X3, GARAGE_Y + GARAGE_L, 0],
    [X3, Y5, 0],
    [X0, Y5, 0],
]
r = call_mcp("createFloor", {"boundaryPoints": floor_pts, "levelId": level_id})
print(f"  Floor: {'OK' if r.get('success') else str(r.get('error', '?'))[:20]}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("FLOOR PLAN COMPLETE!")
print("=" * 70)
print(f"""
Building: {X3:.1f}' × {Y5:.1f}' (plus garage)
Exterior walls: 8"
Interior walls: 4"

Check Revit model for accuracy.
""")
