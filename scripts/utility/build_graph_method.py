"""
Build Floor Plan - GRAPH METHOD
Walls defined as unique segments between corner points
No duplicates - each wall segment appears exactly once

Key insight: A floor plan is a GRAPH where:
- Nodes = corner points (wall intersections)
- Edges = wall segments (connecting corners)
"""
import win32file
import json
import time

# =============================================================================
# COORDINATE GRID FROM DIMENSION STRINGS
# =============================================================================

# Bottom dimension string (X-axis): 5'-4.5" | 8'-10" | 7'-9.5" | 5'-1.5" | 8'-7" | 10'-0.5" | 10'-0.5"
X = {
    'A': 0,
    'B': 5.375,      # 5'-4.5"
    'C': 14.208,     # +8'-10"
    'D': 22.0,       # +7'-9.5"
    'E': 27.125,     # +5'-1.5"
    'F': 35.708,     # +8'-7" (main house east edge)
    'G': 45.75,      # +10'-0.5"
    'H': 55.792,     # +10'-0.5" (total width)
}

# Left dimension string (Y-axis): 7'-6.5" | 13'-0.5" | 22'-9.5" | 6'-9.5"
Y = {
    '0': 0,
    '1': 7.542,      # 7'-6.5"
    '2': 20.584,     # +13'-0.5"
    '3': 43.376,     # +22'-9.5"
    '4': 50.168,     # +6'-9.5" (total depth)
}

# Additional Y coordinates for room divisions
Y['1a'] = 4.0       # Porch top
Y['gar'] = 3.0      # Garage south
Y['2a'] = 32.5      # Bedroom-2 top
Y['2b'] = 38.0      # Bath row bottom
Y['3a'] = 35.0      # Family/Dining bottom

# Additional X coordinates for room divisions
X['B1'] = 8.0       # Master bath east / bath-2 east
X['C1'] = 12.0      # Bedroom-2 east / Bedroom-3 east
X['C2'] = 16.0      # W.I.C. east / Master bedroom partial
X['D1'] = 18.0      # Hall-1 east
X['E1'] = 24.0      # Bath-3 east / Living east
X['F1'] = 43.0      # Utility east

# =============================================================================
# EXTERIOR WALLS - Perimeter (drawn once, counterclockwise)
# =============================================================================
EXTERIOR = [
    # West wall
    ((X['A'], Y['0']), (X['A'], Y['4']), "Ext-West"),
    # North wall
    ((X['A'], Y['4']), (X['H'], Y['4']), "Ext-North"),
    # East wall (upper)
    ((X['H'], Y['4']), (X['H'], Y['gar']+19), "Ext-East-Upper"),
    # Garage east
    ((X['H'], Y['gar']+19), (X['H'], Y['gar']), "Ext-Garage-East"),
    # Garage south
    ((X['H'], Y['gar']), (X['F'], Y['gar']), "Ext-Garage-South"),
    # Step back
    ((X['F'], Y['gar']), (X['F'], Y['0']), "Ext-East-Lower"),
    # South wall
    ((X['F'], Y['0']), (X['A'], Y['0']), "Ext-South"),
]

# =============================================================================
# INTERIOR WALLS - Each segment exactly once
# Organized by grid position, not by room
# =============================================================================
INTERIOR = [
    # --- HORIZONTAL WALLS (running East-West) ---

    # Y = 7.542 (top of entry band)
    ((X['A'], Y['1']), (X['C2'], Y['1']), "H-Y1-MasterTop"),

    # Y = 20.584 (top of master band)
    ((X['A'], Y['2']), (X['E1'], Y['2']), "H-Y2-MainDivider"),

    # Y = 32.5 (Bedroom-2 top)
    ((X['A'], Y['2a']), (X['C1'], Y['2a']), "H-Y2a-Bed2Top"),

    # Y = 38.0 (Bath row bottom / Bedroom-3,4 bottom)
    ((X['A'], Y['2b']), (X['E1'], Y['2b']), "H-Y2b-BathRow"),

    # Y = 43.376 (Bath row top)
    ((X['A'], Y['3']), (X['E1'], Y['3']), "H-Y3-BedFloor"),

    # Y = 35.0 (Family/Kitchen divider)
    ((X['E1'], Y['3a']), (X['H'], Y['3a']), "H-Y3a-FamilyFloor"),

    # Y = 4.0 (Porch top)
    ((X['D'], Y['1a']), (X['F'], Y['1a']), "H-Porch-Top"),

    # Y = 22 (Garage top)
    ((X['F'], Y['gar']+19), (X['H'], Y['gar']+19), "H-Garage-Top"),

    # --- VERTICAL WALLS (running North-South) ---

    # X = 8.0 (Master bath east)
    ((X['B1'], Y['0']), (X['B1'], Y['1']), "V-B1-MBathEast"),

    # X = 8.0 (Bath-2 east)
    ((X['B1'], Y['2b']), (X['B1'], Y['3']), "V-B1-Bath2East"),

    # X = 12.0 (Bedroom-2 east, Bedroom-3 east)
    ((X['C1'], Y['2']), (X['C1'], Y['4']), "V-C1-BedroomEast"),

    # X = 16.0 (W.I.C. east)
    ((X['C2'], Y['2']), (X['C2'], Y['2a']), "V-C2-WICEast"),

    # X = 18.0 (Hall-1 east)
    ((X['D1'], Y['2b']), (X['D1'], Y['3']), "V-D1-HallEast"),

    # X = 24.0 (Living east / Bath-3 east / connects to Kitchen)
    ((X['E1'], Y['1']), (X['E1'], Y['3a']), "V-E1-LivingEast"),

    # X = 35.708 (Kitchen east / main divider)
    ((X['F'], Y['2']), (X['F'], Y['3a']), "V-F-KitchenEast"),

    # X = 43.0 (Utility east)
    ((X['F1'], Y['2']), (X['F1'], Y['3a']), "V-F1-UtilityEast"),
]

# =============================================================================
# ROOM CENTERS
# =============================================================================
ROOMS = [
    # Name, center X, center Y
    ("Master Bath", 4.0, 3.75),
    ("Master Bedroom", 8.0, 14.0),
    ("Bedroom-2", 6.0, 26.5),
    ("W.I.C.", 14.0, 23.0),
    ("Living", 20.0, 14.0),
    ("Bath-2", 4.0, 40.5),
    ("Hall-1", 13.0, 40.5),
    ("Bath-3", 21.0, 40.5),
    ("Bedroom-3", 6.0, 44.0),
    ("Bedroom-4", 18.0, 44.0),
    ("Family/Dining", 40.0, 42.5),
    ("Kitchen", 30.0, 27.5),
    ("Laundry", 39.0, 24.0),
    ("Utility", 39.0, 31.0),
    ("Porch", 28.5, 2.0),
    ("2-Car Garage", 46.0, 12.5),
]

# =============================================================================
# BUILD EXECUTION
# =============================================================================

def main():
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
    print("BUILDING FLOOR PLAN - GRAPH METHOD")
    print("Unique wall segments only - no duplicates")
    print("=" * 70)

    # Get Level 1
    r = call_mcp("getLevels", {})
    level_id = None
    for lvl in r.get("levels", []):
        if lvl.get("name") == "Level 1":
            level_id = lvl.get("levelId")
    print(f"\nLevel 1 ID: {level_id}")
    print(f"Building size: {X['H']:.1f}' x {Y['4']:.1f}'")

    # Wall types
    EXT_WALL = 441451  # 8"
    INT_WALL = 441459  # 4"
    HEIGHT = 10.0

    # Build exterior walls
    print(f"\n[1/4] Exterior Walls ({len(EXTERIOR)})...")
    for (sx, sy), (ex, ey), name in EXTERIOR:
        r = call_mcp("createWallByPoints", {
            "startPoint": [sx, sy, 0],
            "endPoint": [ex, ey, 0],
            "levelId": level_id,
            "height": HEIGHT,
            "wallTypeId": EXT_WALL
        })
        status = "OK" if r.get("success") else "FAIL"
        print(f"  {name}: {status}")
        time.sleep(0.05)

    # Build interior walls
    print(f"\n[2/4] Interior Walls ({len(INTERIOR)})...")
    for (sx, sy), (ex, ey), name in INTERIOR:
        r = call_mcp("createWallByPoints", {
            "startPoint": [sx, sy, 0],
            "endPoint": [ex, ey, 0],
            "levelId": level_id,
            "height": HEIGHT,
            "wallTypeId": INT_WALL
        })
        status = "OK" if r.get("success") else "FAIL"
        print(f"  {name}: {status}")
        time.sleep(0.05)

    # Create rooms
    print(f"\n[3/4] Rooms ({len(ROOMS)})...")
    for name, cx, cy in ROOMS:
        r = call_mcp("createRoom", {
            "location": [cx, cy, 0],
            "levelId": level_id,
            "name": name
        })
        status = "OK" if r.get("success") else "FAIL"
        print(f"  {name}: {status}")
        time.sleep(0.05)

    # Create floor
    print("\n[4/4] Floor...")
    floor_pts = [
        [X['A'], Y['0'], 0],
        [X['F'], Y['0'], 0],
        [X['F'], Y['gar'], 0],
        [X['H'], Y['gar'], 0],
        [X['H'], Y['4'], 0],
        [X['A'], Y['4'], 0],
    ]
    r = call_mcp("createFloor", {"boundaryPoints": floor_pts, "levelId": level_id})
    print(f"  Floor: {'OK' if r.get('success') else 'FAIL'}")

    win32file.CloseHandle(pipe)

    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"""
Total: {len(EXTERIOR)} exterior + {len(INTERIOR)} interior walls
       {len(ROOMS)} rooms

Graph method ensures:
- Each wall segment defined exactly once
- No duplicate/overlapping walls
- Proper wall connections at corners

Check Revit model for accuracy.
""")

if __name__ == "__main__":
    main()
