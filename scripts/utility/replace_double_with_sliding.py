"""
Replace double door at (8.6, 26.8) with Door-Double-Sliding 68" x 80"
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
print("REPLACING DOUBLE DOOR WITH SLIDING DOOR")
print("=" * 60)

# First find the double door at (8.6, 26.8)
print("\n[1] Finding double door at (8.6, 26.8)...")

r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])

target_door = None
target_loc = (8.6, 26.8)

for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        loc = info.get("location", [0, 0, 0])
        # Check if this is near the target location
        if abs(loc[0] - target_loc[0]) < 0.5 and abs(loc[1] - target_loc[1]) < 0.5:
            target_door = {
                "id": door_id,
                "family": info.get("familyName"),
                "type": info.get("typeName"),
                "hostId": info.get("hostId"),
                "location": loc
            }
            print(f"  Found: {info.get('familyName')} - {info.get('typeName')}")
            print(f"    ID: {door_id}")
            print(f"    Host Wall: {info.get('hostId')}")
            print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
            break

if not target_door:
    print("  Double door not found at expected location!")
    win32file.CloseHandle(pipe)
    exit(1)

# Get the sliding door type ID
print("\n[2] Finding Door-Double-Sliding type...")
r = call_mcp("getDoorTypes", {})
sliding_type_id = None

if r.get("success"):
    for dt in r.get("doorTypes", []):
        if "Door-Double-Sliding" in dt.get("familyName", "") and "68" in dt.get("typeName", ""):
            sliding_type_id = dt.get("typeId")
            print(f"  Found: {dt.get('familyName')} - {dt.get('typeName')}")
            print(f"    TypeID: {sliding_type_id}")
            break

if not sliding_type_id:
    print("  Door-Double-Sliding 68\" x 80\" type not found!")
    win32file.CloseHandle(pipe)
    exit(1)

# Delete old door and place new one
print(f"\n[3] Deleting old door {target_door['id']}...")
r = call_mcp("deleteDoorWindow", {"elementId": target_door["id"]})
if r.get("success"):
    print("  Deleted successfully")
else:
    print(f"  Error: {r.get('error', 'Unknown')}")
    win32file.CloseHandle(pipe)
    exit(1)

time.sleep(0.2)

print(f"\n[4] Placing new sliding door...")
loc = target_door["location"]
r = call_mcp("placeDoor", {
    "wallId": target_door["hostId"],
    "location": [loc[0], loc[1], loc[2]],
    "doorTypeId": sliding_type_id
})

if r.get("success"):
    new_id = r.get("doorId")
    print(f"  Placed new sliding door: ID {new_id}")
    print("  SUCCESS!")
else:
    print(f"  Error: {r.get('error', 'Unknown')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("Double door replaced with Door-Double-Sliding 68\" x 80\"")
print("=" * 60)
