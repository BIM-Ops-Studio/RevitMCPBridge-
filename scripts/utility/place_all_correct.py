"""
Place All Doors and Windows with Correct Types
Uses exact type IDs from original model
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
print("PLACING ALL DOORS AND WINDOWS WITH CORRECT TYPES")
print("=" * 70)

# Load extracted data
with open("d:/RevitMCPBridge2026/complete_element_data.json", 'r') as f:
    data = json.load(f)

openings = data.get("openings", [])
garage_doors = data.get("garage_doors", [])
regular_doors = data.get("regular_doors", [])
windows = data.get("windows", [])

print(f"\nLoaded: {len(openings)} openings, {len(garage_doors)} garage, {len(regular_doors)} doors, {len(windows)} windows")

# Get walls for placement
print("\nGetting walls from model...")
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

# Place Door Openings
print("\n[1] Placing Door Openings...")
openings_ok = 0
for d in openings:
    loc = d.get("location", [0,0,0])
    type_id = d.get("typeId")
    type_name = d.get("typeName")

    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": loc,
            "doorTypeId": type_id
        })
        if r.get("success"):
            openings_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - FAIL: {r.get('error', '')[:40]}")
    else:
        print(f"  {type_name} - No wall found")
    time.sleep(0.05)

print(f"Door Openings: {openings_ok}/{len(openings)}")

# Place Garage Door
print("\n[2] Placing Garage Door...")
garage_ok = 0
for d in garage_doors:
    loc = d.get("location", [0,0,0])
    type_id = d.get("typeId")
    type_name = d.get("typeName")

    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": loc,
            "doorTypeId": type_id
        })
        if r.get("success"):
            garage_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} - FAIL: {r.get('error', '')[:40]}")
    time.sleep(0.05)

print(f"Garage Doors: {garage_ok}/{len(garage_doors)}")

# Place Regular Doors
print("\n[3] Placing Regular Doors...")
doors_ok = 0
for d in regular_doors:
    loc = d.get("location", [0,0,0])
    type_id = d.get("typeId")
    type_name = d.get("typeName")

    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeDoor", {
            "wallId": host_wall["id"],
            "location": loc,
            "doorTypeId": type_id
        })
        if r.get("success"):
            doors_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - FAIL: {r.get('error', '')[:40]}")
    else:
        print(f"  {type_name} - No wall found")
    time.sleep(0.05)

print(f"Regular Doors: {doors_ok}/{len(regular_doors)}")

# Place Windows
print("\n[4] Placing Windows...")
windows_ok = 0
for w in windows:
    loc = w.get("location", [0,0,0])
    type_id = w.get("typeId")
    type_name = w.get("typeName")

    host_wall, dist = find_host_wall(loc)
    if host_wall and dist < 2.0:
        r = call_mcp("placeWindow", {
            "wallId": host_wall["id"],
            "location": loc,
            "windowTypeId": type_id
        })
        if r.get("success"):
            windows_ok += 1
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - OK")
        else:
            print(f"  {type_name} at ({loc[0]:.1f}, {loc[1]:.1f}) - FAIL: {r.get('error', '')[:40]}")
    else:
        print(f"  {type_name} - No wall found")
    time.sleep(0.05)

print(f"Windows: {windows_ok}/{len(windows)}")

win32file.CloseHandle(pipe)

# Summary
total_placed = openings_ok + garage_ok + doors_ok + windows_ok
total_expected = len(openings) + len(garage_doors) + len(regular_doors) + len(windows)

print("\n" + "=" * 70)
print("PLACEMENT COMPLETE")
print("=" * 70)
print(f"""
Results:
  Door Openings: {openings_ok}/{len(openings)}
  Garage Doors: {garage_ok}/{len(garage_doors)}
  Regular Doors: {doors_ok}/{len(regular_doors)}
  Windows: {windows_ok}/{len(windows)}

  TOTAL: {total_placed}/{total_expected} elements placed
""")
