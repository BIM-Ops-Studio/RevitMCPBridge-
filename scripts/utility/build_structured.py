"""
Build Floor Plan - STRUCTURED APPROACH
Using Text2BIM methodology: Layout Analysis → Structured Design → Coordinates

Phase 1: Layout analyzed (zones, adjacencies)
Phase 2: Rooms positioned (bounds defined)
Phase 3: Walls calculated (this script)
Phase 4: Build in Revit
"""
import win32file
import json
import time

# =============================================================================
# PHASE 3: COORDINATE CALCULATION
# All measurements in feet, based on structured design
# =============================================================================

# Grid from dimension strings
X_GRID = [0, 5.375, 14.208, 22.0, 27.125, 35.708, 45.75, 55.792]
Y_GRID = [0, 7.542, 20.584, 43.376, 50.168]
GAR_Y = 3.0  # Garage south offset

# Room bounds: (name, x1, y1, x2, y2)
# Calculated from layout analysis and room dimensions
ROOMS = {
    # Row 1: Entry Band
    "Master Bath": (0, 0, 7.792, 7.542),

    # Row 2: Master Band
    "Master Bedroom": (0, 7.542, 16.833, 20.584),

    # Row 3: Middle Band
    "Bedroom-2": (0, 20.584, 11.833, 32.542),
    "W.I.C.": (11.833, 20.584, 15.458, 24.542),
    "Living": (15.458, 7.542, 23.5, 24),
    "Bath-2": (0, 37.5, 7.833, 43.0),
    "Hall-1": (7.833, 37.5, 18.8, 43.0),
    "Bath-3": (18.8, 37.5, 26.75, 43.0),
    "Kitchen": (23.5, 20.584, 35.708, 35.0),
    "Laundry": (35.708, 20.584, 43.0, 27.5),
    "Utility": (35.708, 27.5, 43.0, 35.0),

    # Row 4: Bedroom Band
    "Bedroom-3": (0, 38.335, 11.833, 50.168),
    "Bedroom-4": (11.833, 38.335, 23.791, 50.168),
    "Family/Dining": (23.791, 35.0, 55.792, 50.168),

    # Other
    "Porch": (22.0, 0, 35.708, 4.0),
    "2-Car Garage": (35.708, 3.0, 55.792, 22.0),
}

# =============================================================================
# WALL DEFINITIONS
# Derived from room bounds - each wall segment with start/end points
# =============================================================================

# Exterior walls (8" thick)
EXTERIOR_WALLS = [
    # Main house perimeter (counterclockwise from SW)
    ((0, 0), (0, 50.168), "West"),
    ((0, 50.168), (55.792, 50.168), "North"),
    ((55.792, 50.168), (55.792, 22.0), "East-Upper"),
    ((55.792, 22.0), (55.792, 3.0), "Garage-East"),
    ((55.792, 3.0), (35.708, 3.0), "Garage-South"),
    ((35.708, 3.0), (35.708, 0), "East-Lower"),
    ((35.708, 0), (0, 0), "South"),
]

# Interior walls (4" thick)
# Organized by room boundaries
INTERIOR_WALLS = [
    # === Master Bath boundaries ===
    ((0, 7.542), (7.792, 7.542), "MasterBath-N"),
    ((7.792, 0), (7.792, 7.542), "MasterBath-E"),

    # === Master Bedroom boundaries ===
    ((0, 20.584), (16.833, 20.584), "MasterBed-N"),
    ((16.833, 7.542), (16.833, 20.584), "MasterBed-E"),

    # === Bedroom-2 boundaries ===
    ((0, 32.542), (11.833, 32.542), "Bed2-N"),
    ((11.833, 20.584), (11.833, 32.542), "Bed2-E"),

    # === W.I.C. boundaries ===
    ((11.833, 24.542), (15.458, 24.542), "WIC-N"),
    ((15.458, 20.584), (15.458, 24.542), "WIC-E"),

    # === Living boundaries ===
    ((15.458, 24.0), (23.5, 24.0), "Living-N"),
    ((23.5, 7.542), (23.5, 35.0), "Living-E"),

    # === Bath row (Bath-2, Hall-1, Bath-3) ===
    ((0, 37.5), (26.75, 37.5), "BathRow-S"),
    ((0, 43.0), (26.75, 43.0), "BathRow-N"),
    ((7.833, 37.5), (7.833, 43.0), "Bath2-E"),
    ((18.8, 37.5), (18.8, 43.0), "Hall1-E"),

    # === Bedroom-3 boundaries ===
    ((0, 38.335), (11.833, 38.335), "Bed3-S"),
    ((11.833, 38.335), (11.833, 50.168), "Bed3-E"),

    # === Bedroom-4 boundaries ===
    ((23.791, 38.335), (23.791, 50.168), "Bed4-E"),

    # === Family/Dining boundaries ===
    ((23.791, 35.0), (55.792, 35.0), "Family-S"),

    # === Kitchen boundaries ===
    ((35.708, 20.584), (35.708, 35.0), "Kitchen-E"),

    # === Laundry/Utility boundaries ===
    ((35.708, 27.5), (43.0, 27.5), "Laundry-N"),
    ((43.0, 20.584), (43.0, 35.0), "Utility-E"),

    # === Garage top ===
    ((35.708, 22.0), (55.792, 22.0), "Garage-N"),

    # === Porch top ===
    ((22.0, 4.0), (35.708, 4.0), "Porch-N"),
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
    print("BUILDING FLOOR PLAN - STRUCTURED APPROACH")
    print("Text2BIM Methodology: Analyze > Structure > Calculate > Build")
    print("=" * 70)

    # Get Level 1
    r = call_mcp("getLevels", {})
    level_id = None
    for lvl in r.get("levels", []):
        if lvl.get("name") == "Level 1":
            level_id = lvl.get("levelId")
    print(f"\nLevel 1 ID: {level_id}")

    # Wall types
    EXT_WALL = 441451  # 8"
    INT_WALL = 441459  # 4"
    HEIGHT = 10.0

    # Build exterior walls
    print(f"\n[1/4] Creating {len(EXTERIOR_WALLS)} Exterior Walls (8\")...")
    for (sx, sy), (ex, ey), name in EXTERIOR_WALLS:
        r = call_mcp("createWallByPoints", {
            "startPoint": [sx, sy, 0],
            "endPoint": [ex, ey, 0],
            "levelId": level_id,
            "height": HEIGHT,
            "wallTypeId": EXT_WALL
        })
        status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
        print(f"  {name}: {status}")
        time.sleep(0.05)

    # Build interior walls
    print(f"\n[2/4] Creating {len(INTERIOR_WALLS)} Interior Walls (4\")...")
    for (sx, sy), (ex, ey), name in INTERIOR_WALLS:
        r = call_mcp("createWallByPoints", {
            "startPoint": [sx, sy, 0],
            "endPoint": [ex, ey, 0],
            "levelId": level_id,
            "height": HEIGHT,
            "wallTypeId": INT_WALL
        })
        status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
        print(f"  {name}: {status}")
        time.sleep(0.05)

    # Create rooms at center of each room bounds
    print(f"\n[3/4] Creating {len(ROOMS)} Rooms...")
    for name, (x1, y1, x2, y2) in ROOMS.items():
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        r = call_mcp("createRoom", {
            "location": [cx, cy, 0],
            "levelId": level_id,
            "name": name
        })
        status = "OK" if r.get("success") else str(r.get("error", "?"))[:20]
        print(f"  {name} at ({cx:.1f}, {cy:.1f}): {status}")
        time.sleep(0.05)

    # Create floor
    print("\n[4/4] Creating Floor...")
    floor_pts = [
        [0, 0, 0],
        [35.708, 0, 0],
        [35.708, 3.0, 0],
        [55.792, 3.0, 0],
        [55.792, 50.168, 0],
        [0, 50.168, 0],
    ]
    r = call_mcp("createFloor", {"boundaryPoints": floor_pts, "levelId": level_id})
    print(f"  Floor: {'OK' if r.get('success') else str(r.get('error', '?'))[:20]}")

    win32file.CloseHandle(pipe)

    # Summary
    print("\n" + "=" * 70)
    print("BUILD COMPLETE!")
    print("=" * 70)
    print(f"""
Building: {X_GRID[-1]:.1f}' × {Y_GRID[-1]:.1f}'
Exterior walls: {len(EXTERIOR_WALLS)} (8")
Interior walls: {len(INTERIOR_WALLS)} (4")
Rooms: {len(ROOMS)}

Methodology: Text2BIM structured approach
- Phase 1: Layout analysis (zones, adjacencies)
- Phase 2: Structured design (room bounds)
- Phase 3: Coordinate calculation (wall positions)
- Phase 4: Build execution (this run)

Check Revit model for accuracy.
""")

if __name__ == "__main__":
    main()
