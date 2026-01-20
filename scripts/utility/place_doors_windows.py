"""
Place Doors and Windows in New Model
Uses positions extracted from original model
"""
import win32file
import json
import time
import math

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

def distance_to_wall(point, wall_start, wall_end):
    """Calculate perpendicular distance from point to wall line segment"""
    px, py = point[0], point[1]
    x1, y1 = wall_start[0], wall_start[1]
    x2, y2 = wall_end[0], wall_end[1]

    # Vector from start to end
    dx = x2 - x1
    dy = y2 - y1

    # Length squared
    len_sq = dx*dx + dy*dy
    if len_sq == 0:
        return math.sqrt((px-x1)**2 + (py-y1)**2)

    # Parameter t for projection onto line
    t = max(0, min(1, ((px-x1)*dx + (py-y1)*dy) / len_sq))

    # Closest point on line segment
    cx = x1 + t * dx
    cy = y1 + t * dy

    return math.sqrt((px-cx)**2 + (py-cy)**2)

print("=" * 70)
print("PLACING DOORS AND WINDOWS")
print("=" * 70)

# Load extracted positions
with open("d:/RevitMCPBridge2026/door_window_positions.json", 'r') as f:
    data = json.load(f)

doors = data.get("doors", [])
windows = data.get("windows", [])

print(f"\nLoaded {len(doors)} doors and {len(windows)} windows")

# Get all walls in new model
print("\nGetting walls from new model...")
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"Found {len(walls)} walls")

# Get wall geometry for matching
wall_geometry = []
for wall in walls:
    wall_id = wall.get("id")
    info = call_mcp("getWallInfo", {"wallId": wall_id})
    if info.get("success"):
        wall_geometry.append({
            "id": wall_id,
            "start": info.get("startPoint"),
            "end": info.get("endPoint"),
            "name": info.get("wallType")
        })

print(f"Got geometry for {len(wall_geometry)} walls")

# Function to find host wall for a point
def find_host_wall(location):
    min_dist = float('inf')
    best_wall = None
    for wall in wall_geometry:
        dist = distance_to_wall(location, wall["start"], wall["end"])
        if dist < min_dist:
            min_dist = dist
            best_wall = wall
    return best_wall, min_dist

# Place doors
print("\n[1] Placing Doors...")
doors_ok = 0
doors_fail = 0

for door in doors:
    loc = door.get("location", [0,0,0])
    type_name = door.get("typeName", "Unknown")

    # Find host wall
    host_wall, dist = find_host_wall(loc)

    if host_wall and dist < 2.0:  # Within 2 feet of wall
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": loc
        })

        if r.get("success"):
            doors_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            doors_fail += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - FAIL: {r.get('error', 'Unknown')[:40]}")
    else:
        doors_fail += 1
        print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - No wall found (dist={dist:.1f})")

    time.sleep(0.05)

print(f"\nDoors placed: {doors_ok}/{len(doors)}")

# Place windows
print("\n[2] Placing Windows...")
windows_ok = 0
windows_fail = 0

for window in windows:
    loc = window.get("location", [0,0,0])
    type_name = window.get("typeName", "Unknown")

    # Find host wall
    host_wall, dist = find_host_wall(loc)

    if host_wall and dist < 2.0:
        r = call_mcp("placeWindow", {
            "wallId": host_wall["id"],
            "location": loc
        })

        if r.get("success"):
            windows_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            windows_fail += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - FAIL: {r.get('error', 'Unknown')[:40]}")
    else:
        windows_fail += 1
        print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - No wall found")

    time.sleep(0.05)

print(f"\nWindows placed: {windows_ok}/{len(windows)}")

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70)
print("PLACEMENT COMPLETE")
print("=" * 70)
print(f"""
Results:
  Doors: {doors_ok}/{len(doors)} placed
  Windows: {windows_ok}/{len(windows)} placed

Total: {doors_ok + windows_ok}/{len(doors) + len(windows)} elements
""")
