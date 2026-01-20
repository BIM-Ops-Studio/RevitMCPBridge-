"""
Build PERIMETER ONLY - Based on yellow outline trace
No interior walls - just the exterior perimeter

Shape: Rectangle with entry recess and garage offset
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

print("=" * 60)
print("BUILDING PERIMETER ONLY")
print("Based on yellow outline trace")
print("=" * 60)

# Get Level 1
r = call_mcp("getLevels", {})
level_id = None
for lvl in r.get("levels", []):
    if lvl.get("name") == "Level 1":
        level_id = lvl.get("levelId")
print(f"\nLevel 1 ID: {level_id}")

# Wall type - 8" exterior
EXT_WALL = 441451
HEIGHT = 10.0

# =============================================================================
# PERIMETER COORDINATES
# Based on dimension strings:
# Width: 55'-9.5" = 55.792'
# Depth: ~50'
# Entry recess: ~8' wide, ~6' deep
# Garage offset: Y=3'
# =============================================================================

# Key X positions
X_WEST = 0
X_ENTRY_WEST = 19.0      # Entry recess west edge
X_ENTRY_EAST = 27.0      # Entry recess east edge (~8' wide)
X_GARAGE_WEST = 35.708   # Where garage meets main house
X_EAST = 55.792          # East edge

# Key Y positions
Y_SOUTH = 0
Y_GARAGE = 3.0           # Garage offset
Y_ENTRY_BACK = 6.0       # Entry recess depth
Y_NORTH = 50.168         # North edge

print(f"\nBuilding dimensions: {X_EAST}' x {Y_NORTH}'")
print(f"Entry recess: {X_ENTRY_EAST - X_ENTRY_WEST}' wide x {Y_ENTRY_BACK}' deep")
print(f"Garage offset: {Y_GARAGE}'")

# =============================================================================
# PERIMETER WALLS (10 segments, clockwise from SW)
# =============================================================================

perimeter = [
    # 1. West wall (full height)
    ((X_WEST, Y_SOUTH), (X_WEST, Y_NORTH), "1-West"),

    # 2. North wall (full width)
    ((X_WEST, Y_NORTH), (X_EAST, Y_NORTH), "2-North"),

    # 3. East wall (down to garage level)
    ((X_EAST, Y_NORTH), (X_EAST, Y_GARAGE), "3-East"),

    # 4. Garage south wall
    ((X_EAST, Y_GARAGE), (X_GARAGE_WEST, Y_GARAGE), "4-Garage-South"),

    # 5. Jog down from garage to main level
    ((X_GARAGE_WEST, Y_GARAGE), (X_GARAGE_WEST, Y_SOUTH), "5-Garage-West"),

    # 6. South wall (garage to entry)
    ((X_GARAGE_WEST, Y_SOUTH), (X_ENTRY_EAST, Y_SOUTH), "6-South-East"),

    # 7. Entry east wall (goes up into recess)
    ((X_ENTRY_EAST, Y_SOUTH), (X_ENTRY_EAST, Y_ENTRY_BACK), "7-Entry-East"),

    # 8. Entry back wall
    ((X_ENTRY_EAST, Y_ENTRY_BACK), (X_ENTRY_WEST, Y_ENTRY_BACK), "8-Entry-Back"),

    # 9. Entry west wall (goes down from recess)
    ((X_ENTRY_WEST, Y_ENTRY_BACK), (X_ENTRY_WEST, Y_SOUTH), "9-Entry-West"),

    # 10. South wall (entry to SW corner)
    ((X_ENTRY_WEST, Y_SOUTH), (X_WEST, Y_SOUTH), "10-South-West"),
]

print(f"\n[1/1] Creating {len(perimeter)} Perimeter Walls (8\")...")

for (sx, sy), (ex, ey), name in perimeter:
    r = call_mcp("createWallByPoints", {
        "startPoint": [sx, sy, 0],
        "endPoint": [ex, ey, 0],
        "levelId": level_id,
        "height": HEIGHT,
        "wallTypeId": EXT_WALL
    })
    status = "OK" if r.get("success") else "FAIL"
    length = ((ex-sx)**2 + (ey-sy)**2)**0.5
    print(f"  {name}: ({sx:.1f},{sy:.1f}) to ({ex:.1f},{ey:.1f}) [{length:.1f}'] - {status}")
    time.sleep(0.05)

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("PERIMETER COMPLETE")
print("=" * 60)
print("""
Check Revit model:
- West side (master) extends to Y=0
- East side (garage) stops at Y=3
- Entry recess ~8' wide in the middle
- Total: 55.8' x 50.2'

No interior walls yet - just the perimeter.
""")
