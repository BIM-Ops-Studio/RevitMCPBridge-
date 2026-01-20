"""
Check specific problem doors: double door, closet doors, sliding doors, entry door
"""
import win32file
import json
from collections import defaultdict

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
print("CHECKING PROBLEM DOORS")
print("=" * 60)

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nTotal doors: {len(doors)}")

# Problem door types to check
problem_types = [
    "Double",      # Double door (68" x 80")
    "Bifold",      # Closet bifold doors
    "Sliding",     # Sliding closet doors
    "Entry",       # Front entry door
    "Exterior"     # Entry doors
]

# Gather all door info and check for issues
print("\n[1] PROBLEM DOOR TYPES:")
door_locations = defaultdict(list)

for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        family = info.get("familyName", "")
        type_name = info.get("typeName", "")
        loc = info.get("location", [0, 0, 0])
        host = info.get("hostId")

        loc_key = (round(loc[0], 1), round(loc[1], 1))
        door_locations[loc_key].append({
            "id": door_id,
            "family": family,
            "type": type_name,
            "host": host
        })

        # Check if it's a problem type
        for ptype in problem_types:
            if ptype.lower() in family.lower() or ptype.lower() in type_name.lower():
                print(f"\n  {family} - {type_name}")
                print(f"    ID: {door_id}")
                print(f"    Location: ({loc[0]:.1f}, {loc[1]:.1f})")
                print(f"    Host Wall: {host}")
                break

# Check for any remaining duplicates
print("\n\n[2] CHECKING FOR REMAINING DUPLICATES:")
duplicates_found = False
for loc, door_list in door_locations.items():
    if len(door_list) > 1:
        duplicates_found = True
        print(f"\n  Duplicate at {loc}:")
        for d in door_list:
            print(f"    ID {d['id']}: {d['family']} (Host: {d['host']})")

if not duplicates_found:
    print("  No duplicates found")

# Check walls at problem locations
print("\n\n[3] CHECKING WALLS AT PROBLEM LOCATIONS:")

# Known problem door locations (approximate from original data)
problem_locations = [
    (8.6, 26.8),    # Double door 68" x 80"
    (-6.1, 3.6),    # Bifold 3' - 6" x 6' - 8"
    (-20.4, 14.3),  # Sliding 60" x 80"
    (-20.4, 3.8),   # Sliding 60" x 80"
    (-8.3, -4.6),   # Sliding 48" x 80"
    (7.4, -13.2),   # Entry 36" x 84"
]

# Get all walls
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])

for prob_loc in problem_locations:
    loc_key = (round(prob_loc[0], 1), round(prob_loc[1], 1))
    if loc_key in door_locations:
        for door in door_locations[loc_key]:
            host_id = door.get("host")
            if host_id:
                wall_info = call_mcp("getWallInfo", {"wallId": host_id})
                if wall_info.get("success"):
                    print(f"\n  Door at {loc_key}:")
                    print(f"    Door: {door['family']}")
                    print(f"    Wall ID: {host_id}")
                    print(f"    Wall Type: {wall_info.get('wallTypeName')}")
                    print(f"    Wall Length: {wall_info.get('length'):.2f} ft")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("POTENTIAL ISSUES:")
print("=" * 60)
print("""
If doors aren't cutting:
1. Wall may be too thin for door width
2. Duplicate walls at same location
3. Door family issue

To fix manually:
- Select problem door
- Modify tab > Geometry > Cut
- Click the host wall
""")
