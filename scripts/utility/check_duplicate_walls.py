"""
Check for duplicate/overlapping walls that may prevent door cuts
"""
import win32file
import json
from collections import defaultdict
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

print("=" * 60)
print("CHECKING FOR DUPLICATE/OVERLAPPING WALLS")
print("=" * 60)

# Get all walls
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"\nTotal walls: {len(walls)}")

# Get wall geometry for all walls
wall_data = []
print("\nGathering wall geometry...")

for wall in walls:
    wall_id = wall.get("id")
    info = call_mcp("getWallInfo", {"wallId": wall_id})
    if info.get("success"):
        start = info.get("startPoint", [0, 0, 0])
        end = info.get("endPoint", [0, 0, 0])
        wall_data.append({
            "id": wall_id,
            "start": (round(start[0], 2), round(start[1], 2)),
            "end": (round(end[0], 2), round(end[1], 2)),
            "length": info.get("length", 0)
        })

# Check for overlapping walls (same start/end or very close)
print("\n[1] CHECKING FOR OVERLAPPING WALLS:")

def walls_overlap(w1, w2):
    """Check if two walls overlap or are very close"""
    # Check if endpoints match
    if (w1["start"] == w2["start"] and w1["end"] == w2["end"]) or \
       (w1["start"] == w2["end"] and w1["end"] == w2["start"]):
        return True

    # Check if they're parallel and close
    def point_dist(p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    # Check if any endpoints are very close
    if point_dist(w1["start"], w2["start"]) < 0.5 and point_dist(w1["end"], w2["end"]) < 0.5:
        return True
    if point_dist(w1["start"], w2["end"]) < 0.5 and point_dist(w1["end"], w2["start"]) < 0.5:
        return True

    return False

overlaps_found = False
for i, w1 in enumerate(wall_data):
    for w2 in wall_data[i+1:]:
        if walls_overlap(w1, w2):
            overlaps_found = True
            print(f"\n  Overlap found:")
            print(f"    Wall {w1['id']}: {w1['start']} to {w1['end']} (L={w1['length']:.1f})")
            print(f"    Wall {w2['id']}: {w2['start']} to {w2['end']} (L={w2['length']:.1f})")

if not overlaps_found:
    print("  No overlapping walls found")

# Check walls near problem door locations
print("\n\n[2] WALLS NEAR PROBLEM DOOR LOCATIONS:")

problem_locs = [
    ((8.6, 26.8), "Double door"),
    ((-6.1, 3.6), "Bifold"),
    ((-20.4, 14.3), "Sliding 1"),
    ((-20.4, 3.8), "Sliding 2"),
    ((-8.3, -4.6), "Sliding 3"),
    ((7.4, -13.2), "Entry door"),
]

for loc, name in problem_locs:
    print(f"\n  {name} at {loc}:")
    # Find walls that pass near this point
    nearby_walls = []
    for w in wall_data:
        # Simple check: is point close to line between start and end?
        x, y = loc
        x1, y1 = w["start"]
        x2, y2 = w["end"]

        # Distance from point to line segment
        dx = x2 - x1
        dy = y2 - y1
        len_sq = dx*dx + dy*dy
        if len_sq > 0:
            t = max(0, min(1, ((x-x1)*dx + (y-y1)*dy) / len_sq))
            cx = x1 + t * dx
            cy = y1 + t * dy
            dist = math.sqrt((x-cx)**2 + (y-cy)**2)
            if dist < 2.0:  # Within 2 feet of wall
                nearby_walls.append((w["id"], dist, w["length"]))

    nearby_walls.sort(key=lambda x: x[1])
    for wall_id, dist, length in nearby_walls[:3]:
        print(f"    Wall {wall_id}: dist={dist:.2f} ft, length={length:.1f} ft")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("IF DUPLICATE WALLS FOUND:")
print("=" * 60)
print("""
Delete one of the overlapping walls to allow doors to cut properly.
The door should be hosted on only one wall.

If no duplicates but still not cutting:
1. Door family may not have "Cuts Wall" enabled
2. Try: Select door > Modify > Geometry > Cut > Click wall
""")
