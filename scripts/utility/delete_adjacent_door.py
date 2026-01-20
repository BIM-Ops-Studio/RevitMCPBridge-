"""
Delete the single door adjacent to the sliding door at (8.6, 26.8)
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
print("FINDING SINGLE DOOR ADJACENT TO SLIDING DOOR")
print("=" * 60)

# Get all doors and find ones near y=26.8 (same wall as sliding door)
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])

print(f"\nTotal doors: {len(doors)}")
print("\nDoors near Y=26.8 (same area as sliding door):")

adjacent_doors = []
sliding_door_x = 8.6

for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        loc = info.get("location", [0, 0, 0])
        # Find doors near Y=26.8
        if abs(loc[1] - 26.8) < 1.0:
            door_data = {
                "id": door_id,
                "family": info.get("familyName"),
                "type": info.get("typeName"),
                "location": loc
            }
            adjacent_doors.append(door_data)
            print(f"  ID {door_id}: {info.get('familyName')} - {info.get('typeName')}")
            print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")

# Find the single door (not the sliding door)
door_to_delete = None
for d in adjacent_doors:
    # Skip the sliding door at x=8.6
    if abs(d["location"][0] - sliding_door_x) > 1.0:
        if "Single" in d["family"] or "Single" in d["type"]:
            door_to_delete = d
            break
    # Also check for any non-sliding door
    if "Sliding" not in d["family"] and door_to_delete is None:
        door_to_delete = d

if door_to_delete:
    print(f"\n[DELETING] {door_to_delete['family']} - {door_to_delete['type']}")
    print(f"  ID: {door_to_delete['id']}")
    print(f"  Location: ({door_to_delete['location'][0]:.2f}, {door_to_delete['location'][1]:.2f})")

    r = call_mcp("deleteDoorWindow", {"elementId": door_to_delete["id"]})
    if r.get("success"):
        print("  DELETED successfully!")
    else:
        print(f"  Error: {r.get('error', 'Unknown')}")
else:
    print("\nNo single door found adjacent to sliding door")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
