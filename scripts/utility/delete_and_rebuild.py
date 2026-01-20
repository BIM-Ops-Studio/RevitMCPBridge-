"""
Delete all existing walls, rooms, floors and rebuild fresh
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
print("STEP 1: DELETING EXISTING ELEMENTS")
print("=" * 60)

# Get all walls in the model
print("\n[1/4] Getting all walls...")
r = call_mcp("getWallsInView", {})
wall_ids = []
if r.get("success"):
    walls = r.get("walls", [])
    wall_ids = [w.get("wallId") for w in walls if w.get("wallId")]
    print(f"  Found {len(wall_ids)} walls")
else:
    # Try getting elements by category
    r = call_mcp("getElements", {"categoryName": "Walls"})
    if r.get("success"):
        elements = r.get("elements", [])
        wall_ids = [e.get("elementId") for e in elements if e.get("elementId")]
        print(f"  Found {len(wall_ids)} walls")

# Delete walls
if wall_ids:
    print("\n[2/4] Deleting walls...")
    r = call_mcp("deleteElements", {"elementIds": wall_ids})
    if r.get("success"):
        print(f"  Deleted {len(wall_ids)} walls")
    else:
        print(f"  Error: {r.get('error', 'unknown')}")
else:
    print("\n[2/4] No walls to delete")

# Get and delete rooms
print("\n[3/4] Getting all rooms...")
r = call_mcp("getRooms", {})
room_ids = []
if r.get("success"):
    rooms = r.get("rooms", [])
    room_ids = [rm.get("roomId") for rm in rooms if rm.get("roomId")]
    print(f"  Found {len(room_ids)} rooms")

if room_ids:
    for room_id in room_ids:
        r = call_mcp("deleteRoom", {"roomId": room_id})
    print(f"  Deleted {len(room_ids)} rooms")
else:
    print("  No rooms to delete")

# Get and delete floors
print("\n[4/4] Getting floors...")
r = call_mcp("getElements", {"categoryName": "Floors"})
floor_ids = []
if r.get("success"):
    elements = r.get("elements", [])
    floor_ids = [e.get("elementId") for e in elements if e.get("elementId")]
    print(f"  Found {len(floor_ids)} floors")

if floor_ids:
    r = call_mcp("deleteElements", {"elementIds": floor_ids})
    print(f"  Deleted {len(floor_ids)} floors")
else:
    print("  No floors to delete")

print("\n" + "=" * 60)
print("DELETION COMPLETE")
print("=" * 60)
print("\nModel should now be empty. Check Revit.")
print("Run rebuild_correct.py to create the new model.")

win32file.CloseHandle(pipe)
