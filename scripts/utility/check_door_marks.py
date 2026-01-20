"""
Check specific door marks and their host wall status
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

print("=" * 60)
print("CHECKING DOOR MARKS 171, 172, 174, 175")
print("=" * 60)

# Target marks to find
target_marks = ["171", "172", "174", "175"]

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nTotal doors: {len(doors)}")

# Find doors with these marks
print("\nSearching for target door marks...")
found_doors = []

for door in doors:
    door_id = door.get("id")

    # Get parameters to find the Mark
    params_r = call_mcp("getParameters", {"elementId": door_id})
    if params_r.get("success"):
        params = params_r.get("parameters", [])
        mark = None
        for p in params:
            if p.get("name") == "Mark":
                mark = p.get("value", "")
                break

        if mark in target_marks:
            # Get detailed door info
            info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
            if info.get("success"):
                found_doors.append({
                    "mark": mark,
                    "id": door_id,
                    "family": info.get("familyName"),
                    "type": info.get("typeName"),
                    "hostId": info.get("hostId"),
                    "location": info.get("location", [0, 0, 0])
                })

# Display findings
print(f"\nFound {len(found_doors)} doors with target marks:")

for door in sorted(found_doors, key=lambda x: x["mark"]):
    print(f"\n  Mark {door['mark']}:")
    print(f"    Element ID: {door['id']}")
    print(f"    Family: {door['family']}")
    print(f"    Type: {door['type']}")
    print(f"    Host Wall ID: {door['hostId']}")
    loc = door['location']
    print(f"    Location: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f})")

    # Check if host wall exists
    if door['hostId']:
        wall_info = call_mcp("getWallInfo", {"wallId": door['hostId']})
        if wall_info.get("success"):
            print(f"    Host Wall Length: {wall_info.get('length', 0):.1f} ft")
            print(f"    Wall Start: {wall_info.get('startPoint')}")
            print(f"    Wall End: {wall_info.get('endPoint')}")
        else:
            print(f"    WARNING: Host wall {door['hostId']} not found!")
    else:
        print(f"    WARNING: No host wall!")

# Also list ALL doors with their marks for reference
print("\n\n" + "=" * 60)
print("ALL DOORS WITH MARKS:")
print("=" * 60)

all_door_marks = []
for door in doors:
    door_id = door.get("id")
    params_r = call_mcp("getParameters", {"elementId": door_id})
    if params_r.get("success"):
        params = params_r.get("parameters", [])
        mark = ""
        for p in params:
            if p.get("name") == "Mark":
                mark = p.get("value", "")
                break

        info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
        if info.get("success"):
            all_door_marks.append({
                "mark": mark,
                "id": door_id,
                "family": info.get("familyName", "")[:30],
                "hostId": info.get("hostId")
            })

# Sort by mark and display
for d in sorted(all_door_marks, key=lambda x: x["mark"] if x["mark"] else "zzz"):
    host_status = "OK" if d["hostId"] else "NO HOST!"
    print(f"  Mark {d['mark']:4s} - ID {d['id']} - {d['family'][:25]:25s} - {host_status}")

win32file.CloseHandle(pipe)
