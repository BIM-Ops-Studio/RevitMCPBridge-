"""
Fix Openings - Delete wrong doors and place correct openings
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

print("=" * 70)
print("FIXING OPENINGS AND GARAGE DOOR")
print("=" * 70)

# Positions that should be openings (not regular doors)
opening_positions = [
    ((-10.27, 3.63), "3'-7 1/2\" x 7'-0\""),
    ((-1.94, 1.46), "3'-11 1/2\" x 7'-0\""),
    ((-1.94, 3.63), "3'-7 1/2\" x 7'-0\""),
    ((6.40, 3.63), "12'-3 1/2\" x 7'-0\""),
    ((12.73, 7.13), "11'-11 1/2\" x 7'-0\""),
    ((-10.27, -8.54), "3'-7 1/2\" x 7'-0\""),
    ((5.75, 13.30), "11'-0\" x 7'-0\""),
    ((25.67, 0.96), "6'-10 1/8\" x 7'-0\""),
    ((17.00, 13.30), "48\" x 80\""),
]

# Garage door position
garage_position = ((20.56, -19.49), "192'' x 84''")

# Get all doors in new model
print("\n[1] Getting current doors...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"Found {len(doors)} doors")

# Get door positions
door_positions = []
for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        door_positions.append({
            "id": door_id,
            "location": info.get("location", [0,0,0]),
            "hostId": info.get("hostId"),
            "typeName": info.get("typeName"),
        })

# Find and delete doors at opening/garage positions
print("\n[2] Finding doors to delete...")
doors_to_delete = []

def find_door_at_position(pos, tolerance=0.5):
    for door in door_positions:
        loc = door["location"]
        dist = math.sqrt((loc[0] - pos[0])**2 + (loc[1] - pos[1])**2)
        if dist < tolerance:
            return door
    return None

# Find doors at opening positions
for pos, name in opening_positions:
    door = find_door_at_position(pos)
    if door:
        doors_to_delete.append((door, pos, name, "opening"))
        print(f"  Found door at ({pos[0]:.1f}, {pos[1]:.1f}) - {name} [OPENING]")

# Find door at garage position
door = find_door_at_position(garage_position[0])
if door:
    doors_to_delete.append((door, garage_position[0], garage_position[1], "garage"))
    print(f"  Found door at ({garage_position[0][0]:.1f}, {garage_position[0][1]:.1f}) - {garage_position[1]} [GARAGE]")

print(f"\nFound {len(doors_to_delete)} doors to replace")

# Delete the incorrect doors
print("\n[3] Deleting incorrect doors...")
deleted = 0
for door, pos, name, dtype in doors_to_delete:
    r = call_mcp("deleteElement", {"elementId": door["id"]})
    if r.get("success"):
        deleted += 1
        print(f"  Deleted door at ({pos[0]:.1f}, {pos[1]:.1f})")
    else:
        print(f"  Failed to delete: {r.get('error', 'Unknown')}")
    time.sleep(0.05)

print(f"Deleted {deleted} doors")

# Get walls for placing new elements
print("\n[4] Getting walls for placement...")
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])

wall_geometry = []
for wall in walls:
    wall_id = wall.get("id")
    info = call_mcp("getWallInfo", {"wallId": wall_id})
    if info.get("success"):
        wall_geometry.append({
            "id": wall_id,
            "start": info.get("startPoint"),
            "end": info.get("endPoint"),
        })

def distance_to_wall(point, wall_start, wall_end):
    px, py = point[0], point[1]
    x1, y1 = wall_start[0], wall_start[1]
    x2, y2 = wall_end[0], wall_end[1]
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx*dx + dy*dy
    if len_sq == 0:
        return math.sqrt((px-x1)**2 + (py-y1)**2)
    t = max(0, min(1, ((px-x1)*dx + (py-y1)*dy) / len_sq))
    cx = x1 + t * dx
    cy = y1 + t * dy
    return math.sqrt((px-cx)**2 + (py-cy)**2)

def find_host_wall(location):
    min_dist = float('inf')
    best_wall = None
    for wall in wall_geometry:
        dist = distance_to_wall(location, wall["start"], wall["end"])
        if dist < min_dist:
            min_dist = dist
            best_wall = wall
    return best_wall

# Place openings
print("\n[5] Placing door openings...")
openings_placed = 0

for pos, name in opening_positions:
    host_wall = find_host_wall(pos)
    if host_wall:
        # Place door (will use default door type - user may need to change to opening type)
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": [pos[0], pos[1], 0]
        })
        if r.get("success"):
            openings_placed += 1
            print(f"  Placed opening at ({pos[0]:.1f}, {pos[1]:.1f}) - {name}")
        else:
            print(f"  Failed at ({pos[0]:.1f}, {pos[1]:.1f}): {r.get('error', 'Unknown')[:40]}")
    time.sleep(0.05)

print(f"Openings placed: {openings_placed}/9")

# Place garage door
print("\n[6] Placing garage door...")
pos = garage_position[0]
host_wall = find_host_wall(pos)
if host_wall:
    r = call_mcp("placeDoor", {
        "wallId": host_wall["id"],
        "location": [pos[0], pos[1], 0]
    })
    if r.get("success"):
        print(f"  Placed garage door at ({pos[0]:.1f}, {pos[1]:.1f})")
    else:
        print(f"  Failed: {r.get('error', 'Unknown')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("OPENING FIX COMPLETE")
print("=" * 70)
print(f"""
Results:
  Doors deleted: {deleted}
  Openings placed: {openings_placed}
  Garage door: placed

NOTE: The placed elements use default door types.
You may need to change their types to:
- Door-Opening family for the 9 openings
- Door-Garage family for the garage door
""")
