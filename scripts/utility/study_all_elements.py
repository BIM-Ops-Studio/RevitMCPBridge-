"""
Study All Doors, Windows, Openings - Complete Data Extraction
Get exact types, sizes, and locations for reproduction
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
print("COMPLETE DOOR/WINDOW STUDY")
print("=" * 70)

# Get all doors
print("\n[1] Extracting All Doors...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])

all_doors = []
for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        all_doors.append({
            "id": door_id,
            "familyName": info.get("familyName"),
            "typeName": info.get("typeName"),
            "typeId": info.get("typeId"),
            "hostId": info.get("hostId"),
            "location": info.get("location"),
            "width": info.get("width"),
            "height": info.get("height"),
            "level": info.get("level"),
        })

print(f"Found {len(all_doors)} doors")

# Categorize doors
openings = []
garage_doors = []
regular_doors = []

for d in all_doors:
    family = d.get("familyName", "").lower()
    if "opening" in family:
        openings.append(d)
    elif "garage" in family:
        garage_doors.append(d)
    else:
        regular_doors.append(d)

# Get all windows
print("\n[2] Extracting All Windows...")
r = call_mcp("getElements", {"category": "Windows"})
windows = r.get("result", {}).get("elements", [])

all_windows = []
for window in windows:
    win_id = window.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": win_id})
    if info.get("success"):
        all_windows.append({
            "id": win_id,
            "familyName": info.get("familyName"),
            "typeName": info.get("typeName"),
            "typeId": info.get("typeId"),
            "hostId": info.get("hostId"),
            "location": info.get("location"),
            "width": info.get("width"),
            "height": info.get("height"),
            "level": info.get("level"),
        })

print(f"Found {len(all_windows)} windows")

# Display all data
print("\n" + "=" * 70)
print(f"DOOR OPENINGS ({len(openings)}):")
print("=" * 70)
for d in openings:
    loc = d.get("location", [0,0,0])
    print(f"  Type: {d.get('typeName')}")
    print(f"    Family: {d.get('familyName')}")
    print(f"    TypeID: {d.get('typeId')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print()

print("\n" + "=" * 70)
print(f"GARAGE DOORS ({len(garage_doors)}):")
print("=" * 70)
for d in garage_doors:
    loc = d.get("location", [0,0,0])
    print(f"  Type: {d.get('typeName')}")
    print(f"    Family: {d.get('familyName')}")
    print(f"    TypeID: {d.get('typeId')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print()

print("\n" + "=" * 70)
print(f"REGULAR DOORS ({len(regular_doors)}):")
print("=" * 70)
for d in regular_doors:
    loc = d.get("location", [0,0,0])
    print(f"  Type: {d.get('typeName')}")
    print(f"    Family: {d.get('familyName')}")
    print(f"    TypeID: {d.get('typeId')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print()

print("\n" + "=" * 70)
print(f"WINDOWS ({len(all_windows)}):")
print("=" * 70)
for w in all_windows:
    loc = w.get("location", [0,0,0])
    print(f"  Type: {w.get('typeName')}")
    print(f"    Family: {w.get('familyName')}")
    print(f"    TypeID: {w.get('typeId')}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print()

# Save complete data
output = {
    "openings": openings,
    "garage_doors": garage_doors,
    "regular_doors": regular_doors,
    "windows": all_windows
}

output_file = "d:/RevitMCPBridge2026/complete_element_data.json"
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

win32file.CloseHandle(pipe)

print("=" * 70)
print(f"Complete data saved to: {output_file}")
print("=" * 70)
print(f"""
SUMMARY:
  Door Openings: {len(openings)}
  Garage Doors: {len(garage_doors)}
  Regular Doors: {len(regular_doors)}
  Windows: {len(all_windows)}

  Total Doors: {len(all_doors)}
  Total Windows: {len(all_windows)}
""")
