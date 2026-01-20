"""
Find door mark 179 and replace with correct sliding door type
"""
import win32file
import json
import time

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
print("FINDING DOOR MARK 179 AND SLIDING DOOR TYPES")
print("=" * 60)

# Get all doors
print("\n[1] Finding door mark 179...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])

target_door = None
for door in doors:
    door_id = door.get("id")
    params_r = call_mcp("getParameters", {"elementId": door_id})
    if params_r.get("success"):
        params = params_r.get("parameters", [])
        mark = None
        for p in params:
            if p.get("name") == "Mark":
                mark = p.get("value", "")
                break

        if mark == "179":
            info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
            if info.get("success"):
                target_door = {
                    "id": door_id,
                    "mark": mark,
                    "family": info.get("familyName"),
                    "type": info.get("typeName"),
                    "typeId": info.get("typeId"),
                    "hostId": info.get("hostId"),
                    "location": info.get("location", [0, 0, 0])
                }
                print(f"  Found door mark 179:")
                print(f"    Element ID: {door_id}")
                print(f"    Family: {info.get('familyName')}")
                print(f"    Type: {info.get('typeName')}")
                print(f"    Type ID: {info.get('typeId')}")
                print(f"    Host Wall: {info.get('hostId')}")
                loc = info.get('location', [0,0,0])
                print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})")
            break

if not target_door:
    print("  Door mark 179 not found!")
    win32file.CloseHandle(pipe)
    exit(1)

# Get available door types - look for sliding
print("\n[2] Available sliding door types:")
r = call_mcp("getDoorTypes", {})
sliding_types = []

if r.get("success"):
    door_types = r.get("doorTypes", [])
    for dt in door_types:
        family = dt.get("familyName", "").lower()
        type_name = dt.get("typeName", "").lower()
        if "slid" in family or "slid" in type_name:
            sliding_types.append(dt)
            print(f"  {dt.get('familyName')} - {dt.get('typeName')}")
            print(f"    TypeID: {dt.get('typeId')}")

    print(f"\n  Total door types available: {len(door_types)}")

# Show all door types for reference
print("\n\n[3] ALL DOOR TYPES (for reference):")
if r.get("success"):
    for dt in door_types:
        print(f"  {dt.get('typeId')}: {dt.get('familyName')} - {dt.get('typeName')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
if sliding_types:
    print("Available sliding door type IDs to use:")
    for st in sliding_types:
        print(f"  {st.get('typeId')}: {st.get('familyName')} - {st.get('typeName')}")
print("=" * 60)
