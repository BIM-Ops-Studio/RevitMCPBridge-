"""
List all doors with their marks and types
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
print("ALL DOORS WITH MARKS AND TYPES")
print("=" * 60)

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nTotal doors: {len(doors)}\n")

all_doors = []
for door in doors:
    door_id = door.get("id")

    # Get mark
    params_r = call_mcp("getParameters", {"elementId": door_id})
    mark = ""
    if params_r.get("success"):
        params = params_r.get("parameters", [])
        for p in params:
            if p.get("name") == "Mark":
                mark = p.get("value", "")
                break

    # Get door info
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        all_doors.append({
            "mark": mark,
            "id": door_id,
            "family": info.get("familyName", ""),
            "type": info.get("typeName", ""),
            "typeId": info.get("typeId"),
            "location": info.get("location", [0, 0, 0])
        })

# Sort by mark and display
for d in sorted(all_doors, key=lambda x: x["mark"] if x["mark"] else "zzz"):
    loc = d['location']
    print(f"Mark {d['mark']:4s} | ID {d['id']:7d} | {d['family'][:25]:25s} | {d['type'][:20]:20s} | ({loc[0]:.1f}, {loc[1]:.1f})")

# Also list sliding door types
print("\n\n" + "=" * 60)
print("AVAILABLE SLIDING DOOR TYPES")
print("=" * 60)

r = call_mcp("getDoorTypes", {})
if r.get("success"):
    door_types = r.get("doorTypes", [])
    for dt in door_types:
        family = dt.get("familyName", "").lower()
        type_name = dt.get("typeName", "").lower()
        if "slid" in family or "slid" in type_name:
            print(f"  {dt.get('typeId')}: {dt.get('familyName')} - {dt.get('typeName')}")

win32file.CloseHandle(pipe)
