"""
Find Door Openings vs Regular Doors
Identify cased openings by family name
"""
import win32file
import json

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
print("ANALYZING DOORS - FINDING OPENINGS")
print("=" * 70)

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nFound {len(doors)} door elements")

# Get detailed info for each
openings = []
regular_doors = []
garage_doors = []

for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})

    if info.get("success"):
        family_name = info.get("familyName", "").lower()
        type_name = info.get("typeName", "")
        location = info.get("location", [0,0,0])
        width = info.get("width", 0)
        height = info.get("height", 0)
        type_id = info.get("typeId")
        host_id = info.get("hostId")

        door_info = {
            "id": door_id,
            "familyName": info.get("familyName"),
            "typeName": type_name,
            "typeId": type_id,
            "hostId": host_id,
            "location": location,
            "width": width,
            "height": height,
        }

        # Categorize
        if "opening" in family_name or "cased" in family_name:
            openings.append(door_info)
        elif "garage" in family_name or width > 8:  # Garage doors are typically > 8'
            garage_doors.append(door_info)
        else:
            regular_doors.append(door_info)

# Display results
print("\n" + "=" * 70)
print(f"OPENINGS (Cased Openings): {len(openings)}")
print("=" * 70)
for d in openings:
    loc = d.get("location", [0,0,0])
    width_in = d.get("width", 0) * 12
    height_in = d.get("height", 0) * 12
    print(f"  {d.get('familyName')} - {d.get('typeName')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print(f"    Size: {width_in:.0f}\" x {height_in:.0f}\"")
    print(f"    Type ID: {d.get('typeId')}")
    print()

print("\n" + "=" * 70)
print(f"GARAGE DOORS: {len(garage_doors)}")
print("=" * 70)
for d in garage_doors:
    loc = d.get("location", [0,0,0])
    width_in = d.get("width", 0) * 12
    height_in = d.get("height", 0) * 12
    print(f"  {d.get('familyName')} - {d.get('typeName')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print(f"    Size: {width_in:.0f}\" x {height_in:.0f}\"")
    print(f"    Type ID: {d.get('typeId')}")
    print()

print("\n" + "=" * 70)
print(f"REGULAR DOORS: {len(regular_doors)}")
print("=" * 70)
for d in regular_doors:
    loc = d.get("location", [0,0,0])
    width_in = d.get("width", 0) * 12
    height_in = d.get("height", 0) * 12
    print(f"  {d.get('familyName')} - {d.get('typeName')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print(f"    Size: {width_in:.0f}\" x {height_in:.0f}\"")
    print(f"    Type ID: {d.get('typeId')}")
    print()

# Save data
output = {
    "openings": openings,
    "garage_doors": garage_doors,
    "regular_doors": regular_doors
}

with open("d:/RevitMCPBridge2026/door_analysis.json", 'w') as f:
    json.dump(output, f, indent=2)

win32file.CloseHandle(pipe)

print("=" * 70)
print("Data saved to: door_analysis.json")
print("=" * 70)
print(f"""
SUMMARY:
  Openings: {len(openings)}
  Garage Doors: {len(garage_doors)}
  Regular Doors: {len(regular_doors)}
  Total: {len(openings) + len(garage_doors) + len(regular_doors)}
""")
