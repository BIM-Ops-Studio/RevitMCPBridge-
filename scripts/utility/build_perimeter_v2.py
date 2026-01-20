"""
Build PERIMETER v2 - Corrected based on feedback
- Only ONE recess (front entry)
- NO garage offset - east wall goes straight to Y=0
- Master side is BIGGER (entry positioned toward garage side)
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
print("BUILDING PERIMETER v2")
print("Rectangle with ONE entry recess - no garage offset")
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
# PERIMETER COORDINATES - Corrected
# Rectangle: 55.792' x 50.168'
# One entry recess positioned toward the east (garage side)
# Master side (west) is bigger than garage side (east)
# =============================================================================

# Building dimensions
X_EAST = 55.792
Y_NORTH = 50.168

# Entry recess - positioned toward east so master side is bigger
X_ENTRY_WEST = 35.0      # Entry starts at X=35
X_ENTRY_EAST = 43.0      # Entry ends at X=43 (8' wide)
Y_ENTRY_BACK = 9.33      # Entry depth ~9'-4"

# Resulting sides:
# Master side (west of entry): 35'
# Garage side (east of entry): 55.792 - 43 = 12.792'

print(f"\nBuilding: {X_EAST}' x {Y_NORTH}'")
print(f"Entry recess: {X_ENTRY_EAST - X_ENTRY_WEST}' wide x {Y_ENTRY_BACK}' deep")
print(f"Master side (west): {X_ENTRY_WEST}'")
print(f"Garage side (east): {X_EAST - X_ENTRY_EAST}'")

# =============================================================================
# PERIMETER WALLS (8 segments - rectangle with one recess)
# =============================================================================

perimeter = [
    # 1. West wall (full height)
    ((0, 0), (0, Y_NORTH), "1-West"),

    # 2. North wall (full width)
    ((0, Y_NORTH), (X_EAST, Y_NORTH), "2-North"),

    # 3. East wall (full height - NO offset)
    ((X_EAST, Y_NORTH), (X_EAST, 0), "3-East"),

    # 4. South wall (east of entry)
    ((X_EAST, 0), (X_ENTRY_EAST, 0), "4-South-East"),

    # 5. Entry east wall (goes up into recess)
    ((X_ENTRY_EAST, 0), (X_ENTRY_EAST, Y_ENTRY_BACK), "5-Entry-East"),

    # 6. Entry back wall
    ((X_ENTRY_EAST, Y_ENTRY_BACK), (X_ENTRY_WEST, Y_ENTRY_BACK), "6-Entry-Back"),

    # 7. Entry west wall (goes down from recess)
    ((X_ENTRY_WEST, Y_ENTRY_BACK), (X_ENTRY_WEST, 0), "7-Entry-West"),

    # 8. South wall (west of entry - master side)
    ((X_ENTRY_WEST, 0), (0, 0), "8-South-West"),
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
print("PERIMETER v2 COMPLETE")
print("=" * 60)
print(f"""
Check Revit model:
- Rectangle with ONE entry recess
- East wall goes straight to Y=0 (no garage offset)
- Master side (west): {X_ENTRY_WEST}' - BIGGER
- Garage side (east): {X_EAST - X_ENTRY_EAST:.1f}' - smaller
- Entry: {X_ENTRY_EAST - X_ENTRY_WEST}' wide x {Y_ENTRY_BACK}' deep
""")
