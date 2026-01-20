"""
Find door D10 (sliding door) in original model
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
print("FINDING DOOR D10 IN ORIGINAL MODEL")
print("=" * 60)

# Get all doors
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"\nTotal doors in original model: {len(doors)}")

# Find door D10 and list all sliding doors
print("\nSearching for door D10 and all sliding doors...")

found_d10 = False
sliding_doors = []

for door in doors:
    door_id = door.get("id")

    # Get door info first (this is more reliable)
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if not info.get("success"):
        continue

    family = info.get("familyName", "")
    type_name = info.get("typeName", "")
    loc = info.get("location", [0, 0, 0])

    # Check if it's a sliding door
    if "slid" in family.lower() or "slid" in type_name.lower():
        door_data = {
            "id": door_id,
            "family": family,
            "type": type_name,
            "typeId": info.get("typeId"),
            "hostId": info.get("hostId"),
            "location": loc
        }
        sliding_doors.append(door_data)

        # Try to get mark
        try:
            params_r = call_mcp("getParameters", {"elementId": door_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                for p in params:
                    if p.get("name") == "Mark":
                        door_data["mark"] = p.get("value", "")
                        if p.get("value") == "D10":
                            found_d10 = True
                            print(f"\n*** FOUND DOOR D10 ***")
                            print(f"  Element ID: {door_id}")
                            print(f"  Family: {family}")
                            print(f"  Type: {type_name}")
                            print(f"  Type ID: {info.get('typeId')}")
                            print(f"  Location: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})")
                            print(f"  Host Wall ID: {info.get('hostId')}")
                        break
        except:
            pass

# Show all sliding doors
print(f"\n\nAll sliding doors found: {len(sliding_doors)}")
for sd in sliding_doors:
    mark = sd.get("mark", "no mark")
    loc = sd["location"]
    print(f"  ID {sd['id']}: {sd['family']} - {sd['type']}")
    print(f"    Mark: {mark}, TypeID: {sd['typeId']}, Loc: ({loc[0]:.1f}, {loc[1]:.1f})")

if not found_d10:
    print("\n*** Door D10 not found by mark ***")
    print("The sliding door type ID above can be used to place in new model")

# Also get sliding door types available
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
