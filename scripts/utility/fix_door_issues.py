"""
Fix door issues - check for duplicates and sill heights
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
print("CHECKING FOR DUPLICATE DOORS AND SILL HEIGHTS")
print("=" * 60)

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nFound {len(doors)} total doors")

# Get detailed info for all doors
door_locations = defaultdict(list)
door_details = []

print("\nGathering door details...")
for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        loc = info.get("location", [0, 0, 0])
        loc_key = (round(loc[0], 1), round(loc[1], 1))
        door_locations[loc_key].append({
            "id": door_id,
            "family": info.get("familyName"),
            "type": info.get("typeName"),
            "location": loc
        })
        door_details.append({
            "id": door_id,
            "family": info.get("familyName"),
            "type": info.get("typeName"),
            "location": loc_key
        })

# Check for duplicates
print("\n[1] DUPLICATE LOCATIONS:")
duplicates_found = False
for loc, door_list in door_locations.items():
    if len(door_list) > 1:
        duplicates_found = True
        print(f"\n  Location {loc}:")
        for d in door_list:
            print(f"    ID {d['id']}: {d['family']} - {d['type']}")

if not duplicates_found:
    print("  No duplicates found")

# Count by family type
print("\n[2] DOORS BY FAMILY:")
family_counts = defaultdict(int)
for d in door_details:
    family_counts[d["family"]] += 1

for family, count in sorted(family_counts.items()):
    print(f"  {family}: {count}")

# Check sill height on first door of each type
print("\n[3] CHECKING SILL HEIGHTS:")
checked_families = set()
for door in doors[:10]:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        family = info.get("familyName", "")
        if family not in checked_families:
            checked_families.add(family)

            # Get all parameters
            params_r = call_mcp("getParameters", {"elementId": door_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                sill_found = False
                for p in params:
                    name = p.get("name", "").lower()
                    if "sill" in name:
                        print(f"  {family}: {p.get('name')} = {p.get('value')}")
                        sill_found = True
                if not sill_found:
                    print(f"  {family}: No sill parameter found")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)

if len(doors) > 26:
    print(f"""
NOTE: You have {len(doors)} doors but only 26 were supposed to be placed.
The extra {len(doors) - 26} doors might be from earlier test placements.

To fix in Revit:
1. Select all doors (filter by category)
2. Look for duplicates at the same location
3. Delete the extras

Or use the MCP deleteDoorWindow method to clean up.
""")
else:
    print("""
If doors still aren't cutting walls, try in Revit:
1. Select a problem door
2. Check Sill Height in Properties (should be 0' - 0")
3. Use Modify > Geometry > Cut to manually cut
4. Or check the wall's "Function" parameter
""")
