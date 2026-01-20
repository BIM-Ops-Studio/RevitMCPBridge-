"""
Delete duplicate doors that are interfering with wall cuts
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
print("DELETING DUPLICATE DOORS")
print("=" * 60)

# IDs of duplicates to delete (older ones from test placements)
duplicates_to_delete = [
    1252583,  # Door at (30.2, -1.4)
    1252585,  # Opening at (-10.3, 3.6)
    1252588,  # Opening at (-1.9, 1.5)
    1252593,  # Opening at (6.4, 3.6)
    1252596,  # Opening at (12.7, 7.1)
    1252608,  # Opening at (5.8, 13.3)
    1252611,  # Opening at (25.7, 1.0)
    1252614,  # Opening at (17.0, 13.3)
    1252617,  # Garage at (20.6, -19.5)
]

print(f"\nDeleting {len(duplicates_to_delete)} duplicate doors...")

deleted = 0
for door_id in duplicates_to_delete:
    r = call_mcp("deleteDoorWindow", {"elementId": door_id})
    if r.get("success"):
        deleted += 1
        print(f"  Deleted door {door_id} - OK")
    else:
        print(f"  Failed to delete {door_id}: {r.get('error', 'Unknown error')}")

win32file.CloseHandle(pipe)

print(f"\nDeleted {deleted}/{len(duplicates_to_delete)} duplicates")

# Verify count
print("\nVerifying door count...")
pipe2 = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None, win32file.OPEN_EXISTING, 0, None
)

def call_mcp2(method, params={}):
    request = json.dumps({'method': method, 'params': params}) + '\n'
    win32file.WriteFile(pipe2, request.encode())
    chunks = []
    while True:
        result, data = win32file.ReadFile(pipe2, 65536)
        chunks.append(data)
        combined = b''.join(chunks).decode()
        if combined.strip().endswith('}') or combined.strip().endswith(']'):
            break
        if len(data) < 1024:
            break
    return json.loads(b''.join(chunks).decode().strip())

r = call_mcp2("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"Now have {len(doors)} doors (should be ~27: 9 openings + 1 garage + 16 doors + 1 extra from test)")

win32file.CloseHandle(pipe2)

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("""
1. Check Revit - the doors should now cut properly
2. If some still don't cut, try:
   - Select the door
   - Modify tab > Geometry > Cut
   - Click the wall
""")
