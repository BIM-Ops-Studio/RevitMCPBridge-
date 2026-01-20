"""
Re-host problem doors by deleting and re-placing them
This fixes hosting issues where doors aren't cutting walls
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
print("RE-HOSTING PROBLEM DOORS")
print("=" * 60)

# Problem doors identified earlier (specialty types that aren't cutting)
problem_doors = [
    {"id": 1252915, "name": "Double door 68x80", "loc": (8.6, 26.8)},
    {"id": 1252908, "name": "Bifold 3'-6\" x 6'-8\"", "loc": (-6.1, 3.6)},
    {"id": 1252910, "name": "Sliding 60x80 #1", "loc": (-20.4, 14.3)},
    {"id": 1252912, "name": "Sliding 60x80 #2", "loc": (-20.4, 3.8)},
    {"id": 1252913, "name": "Sliding 48x80", "loc": (-8.3, -4.6)},
    {"id": 1252906, "name": "Entry door 36x84", "loc": (7.4, -13.2)},
]

# First, gather current info for each door
print("\n[1] Gathering current door information...")
doors_to_rehost = []

for door in problem_doors:
    door_id = door["id"]
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})

    if info.get("success"):
        doors_to_rehost.append({
            "id": door_id,
            "name": door["name"],
            "typeId": info.get("typeId"),
            "hostId": info.get("hostId"),
            "location": info.get("location", [0, 0, 0]),
            "family": info.get("familyName"),
            "typeName": info.get("typeName")
        })
        print(f"  {door['name']}: Type {info.get('typeId')}, Wall {info.get('hostId')}")
    else:
        print(f"  {door['name']}: NOT FOUND (may have different ID)")

print(f"\nFound {len(doors_to_rehost)} doors to re-host")

# Delete and re-place each door
print("\n[2] Re-hosting doors...")
success_count = 0

for door in doors_to_rehost:
    print(f"\n  Processing {door['name']}...")

    # Delete the door
    r = call_mcp("deleteDoorWindow", {"elementId": door["id"]})
    if r.get("success"):
        print(f"    Deleted old door {door['id']}")
        time.sleep(0.1)

        # Re-place at same location
        loc = door["location"]
        r = call_mcp("placeDoor", {
            "wallId": door["hostId"],
            "location": [loc[0], loc[1], loc[2]],
            "doorTypeId": door["typeId"]
        })

        if r.get("success"):
            new_id = r.get("doorId")
            print(f"    Created new door {new_id} - OK")
            success_count += 1
        else:
            print(f"    FAILED to re-place: {r.get('error', 'Unknown')[:50]}")
    else:
        print(f"    FAILED to delete: {r.get('error', 'Unknown')[:50]}")

    time.sleep(0.1)

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print(f"RE-HOSTING COMPLETE: {success_count}/{len(doors_to_rehost)} doors")
print("=" * 60)

if success_count == len(doors_to_rehost):
    print("\nAll doors successfully re-hosted!")
    print("Check Revit - the doors should now cut the walls properly.")
else:
    print("\nSome doors failed. Check Revit for any issues.")
