"""
Place All Elements Using New Model Type IDs
Maps original types to available types in new model
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

print("=" * 70)
print("PLACING ALL ELEMENTS WITH CORRECT NEW MODEL TYPE IDS")
print("=" * 70)

# Type ID mappings for NEW MODEL
# Door Openings
OPENING_TYPES = {
    '3\'-7 1/2" x 7\'-0"': 1251072,
    '3\'-11 1/2" x 7\'-0"': 1251070,
    '12\'-3 1/2" x 7\'-0"': 1251068,
    '11\'-11 1/2" x 7\'-0"': 1251066,
    '11\'-0" x 7\'-0"': 1251064,
    '6\'-10 1/8" x 7\'-0"': 1251062,
    '48" x 80"': 1251088,
}

# Garage Door
GARAGE_TYPE = 1243424  # 192'' x 84''

# Regular Doors (mapping to available types)
DOOR_TYPES = {
    '32" x 80"': 387954,      # Door-Passage-Single-Flush 30" x 80" (closest)
    '36" x 80"': 387958,      # Door-Passage-Single-Flush 36" x 80"
    '30" x 80"': 387954,      # Door-Passage-Single-Flush 30" x 80"
    '36" x 84"': 1247250,     # Door-Exterior-Single-Entry 36" x 84"
    '3\' - 6" x 6\' - 8"': 1250189,  # Door-Bifold 3' - 6" x 6' - 8"
    '60" x 80"': 1249183,     # Door-Interior-Double-Sliding 60" x 80"
    '48" x 80"': 1249179,     # Door-Interior-Double-Sliding 48" x 80"
    '68" x 80"': 456430,      # Door-Passage-Double-Flush 68" x 80"
    'pocket': 1252549,        # Door-Interior-Single-Pocket 36" x 80"
}

# Windows - use Fixed windows as placeholder (original had Double-Hung 37x63 and 36x36)
WINDOW_37x63 = 479449    # Window-Fixed 36" x 65" (closest to 37x63)
WINDOW_36x36 = 479439    # Window-Fixed 24" x 36" (closest to 36x36)
WINDOW_SIDELIGHT = 479441  # Window-Fixed 24" x 60" (for sidelight)

# Get walls
print("\nGetting walls...")
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

print(f"Got {len(wall_geometry)} walls")

def find_host_wall(location):
    min_dist = float('inf')
    best_wall = None
    for wall in wall_geometry:
        dist = distance_to_wall(location, wall["start"], wall["end"])
        if dist < min_dist:
            min_dist = dist
            best_wall = wall
    return best_wall, min_dist

# Door Openings to place
openings_data = [
    ((-10.27, 3.63), '3\'-7 1/2" x 7\'-0"'),
    ((-1.94, 1.46), '3\'-11 1/2" x 7\'-0"'),
    ((-1.94, 3.63), '3\'-7 1/2" x 7\'-0"'),
    ((6.40, 3.63), '12\'-3 1/2" x 7\'-0"'),
    ((12.73, 7.13), '11\'-11 1/2" x 7\'-0"'),
    ((-10.27, -8.54), '3\'-7 1/2" x 7\'-0"'),
    ((5.75, 13.30), '11\'-0" x 7\'-0"'),
    ((25.67, 0.96), '6\'-10 1/8" x 7\'-0"'),
    ((17.00, 13.30), '48" x 80"'),
]

# Regular Doors to place
doors_data = [
    ((-14.27, 14.30), '32" x 80"'),
    ((-14.08, 3.80), '32" x 80"'),
    ((-10.27, -0.70), '32" x 80"'),
    ((-7.27, -15.19), '32" x 80"'),
    ((24.17, 13.30), '36" x 80"'),
    ((24.17, 7.96), '36" x 80"'),
    ((-1.94, 6.13), '30" x 80"'),
    ((7.43, -13.16), '36" x 84"'),
    ((-6.10, 3.63), '3\' - 6" x 6\' - 8"'),
    ((-20.38, 14.30), '60" x 80"'),
    ((-20.38, 3.80), '60" x 80"'),
    ((-8.27, -4.62), '48" x 80"'),
    ((8.56, 26.76), '68" x 80"'),
    ((30.19, -1.39), '36" x 80"'),
    ((-5.17, -12.92), 'pocket'),
    ((-16.27, 7.73), '30" x 80"'),
]

# Garage door
garage_data = [((20.56, -19.49), '192" x 84"')]

# Windows to place
windows_data = [
    ((-19.80, -22.49), '37x63'),
    ((-10.96, -22.49), '37x63'),
    ((-3.19, -22.49), '36x36'),
    ((-24.73, -15.40), '37x63'),
    ((-24.73, -2.37), '37x63'),
    ((-24.73, 20.41), '37x63'),
    ((-18.44, 26.76), '37x63'),
    ((-6.10, 26.76), '37x63'),
    ((30.19, 20.19), '37x63'),
    ((30.19, -10.56), '36x36'),
    ((4.84, -13.16), 'sidelight'),
    ((23.23, 26.76), '37x63'),
    ((19.81, 26.76), '37x63'),
    ((-24.73, 8.82), '36x36'),
]

# Place Door Openings
print("\n[1] Placing Door Openings...")
openings_ok = 0
for loc, type_name in openings_data:
    type_id = OPENING_TYPES.get(type_name)
    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0 and type_id:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": [loc[0], loc[1], 0],
            "doorTypeId": type_id
        })
        if r.get("success"):
            openings_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} - FAIL: {r.get('error', '')[:40]}")
    else:
        print(f"  {type_name} - No wall or type")
    time.sleep(0.05)
print(f"Openings: {openings_ok}/9")

# Place Garage Door
print("\n[2] Placing Garage Door...")
garage_ok = 0
for loc, name in garage_data:
    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": [loc[0], loc[1], 0],
            "doorTypeId": GARAGE_TYPE
        })
        if r.get("success"):
            garage_ok += 1
            print(f"  Garage door at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  Garage door - FAIL: {r.get('error', '')[:40]}")
    time.sleep(0.05)
print(f"Garage: {garage_ok}/1")

# Place Regular Doors
print("\n[3] Placing Regular Doors...")
doors_ok = 0
for loc, type_name in doors_data:
    type_id = DOOR_TYPES.get(type_name)
    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0 and type_id:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": [loc[0], loc[1], 0],
            "doorTypeId": type_id
        })
        if r.get("success"):
            doors_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} - FAIL: {r.get('error', '')[:40]}")
    else:
        print(f"  {type_name} - No wall or type")
    time.sleep(0.05)
print(f"Doors: {doors_ok}/16")

# Place Windows
print("\n[4] Placing Windows...")
windows_ok = 0
for loc, type_name in windows_data:
    if type_name == '37x63':
        type_id = WINDOW_37x63
    elif type_name == '36x36':
        type_id = WINDOW_36x36
    else:
        type_id = WINDOW_SIDELIGHT

    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeWindow", {
            "wallId": host_wall["id"],
            "location": [loc[0], loc[1], 0],
            "windowTypeId": type_id
        })
        if r.get("success"):
            windows_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} - FAIL: {r.get('error', '')[:40]}")
    time.sleep(0.05)
print(f"Windows: {windows_ok}/14")

win32file.CloseHandle(pipe)

total = openings_ok + garage_ok + doors_ok + windows_ok
print("\n" + "=" * 70)
print("PLACEMENT COMPLETE")
print("=" * 70)
print(f"""
Results:
  Door Openings: {openings_ok}/9
  Garage Door: {garage_ok}/1
  Regular Doors: {doors_ok}/16
  Windows: {windows_ok}/14

  TOTAL: {total}/40 elements
""")
