"""
Extract All Room Data
Gets room names, areas, and attempts to get boundaries
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
print("EXTRACTING ROOM DATA")
print("=" * 70)

# Get room list
r = call_mcp("getElements", {"category": "Rooms"})
rooms = r.get("result", {}).get("elements", [])
print(f"\nFound {len(rooms)} rooms")

# Try to get detailed room info
room_data = []

# Try getRoomInfo or getRoomBoundary methods
for room in rooms:
    room_id = room.get("id")
    room_name = room.get("name", "Unknown")

    # Try getRoomInfo
    try:
        r = call_mcp("getRoomInfo", {"roomId": room_id})
        if r.get("success"):
            room_info = {
                "id": room_id,
                "name": r.get("name", room_name),
                "number": r.get("number"),
                "level": r.get("level"),
                "area": r.get("area"),
                "perimeter": r.get("perimeter"),
                "volume": r.get("volume"),
                "height": r.get("height"),
                "center": r.get("center"),
                "boundary": r.get("boundary", [])
            }
            room_data.append(room_info)
        else:
            # Fallback - just use basic info
            room_data.append({
                "id": room_id,
                "name": room_name,
                "level": room.get("level")
            })
    except Exception as e:
        print(f"  Room {room_id}: Error - {e}")
        room_data.append({
            "id": room_id,
            "name": room_name,
            "level": room.get("level")
        })

# Display rooms
print("\n" + "=" * 70)
print("ROOM LIST:")
print("=" * 70)

for r in room_data:
    name = r.get("name", "Unknown")
    area = r.get("area", 0)
    level = r.get("level", "?")
    center = r.get("center")

    if area and area > 0:
        print(f"\n  {name}")
        print(f"    Level: {level}")
        print(f"    Area: {area:.1f} SF")
        if center:
            print(f"    Center: ({center[0]:.2f}, {center[1]:.2f})")
        boundary = r.get("boundary", [])
        if boundary:
            print(f"    Boundary points: {len(boundary)}")
            for pt in boundary[:4]:  # Show first 4 points
                print(f"      ({pt[0]:.2f}, {pt[1]:.2f})")
            if len(boundary) > 4:
                print(f"      ... and {len(boundary)-4} more points")
    else:
        print(f"\n  {name} - {level}")

# Save all data
output_file = "d:/RevitMCPBridge2026/all_rooms_data.json"
with open(output_file, 'w') as f:
    json.dump(room_data, f, indent=2)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print(f"Complete room data saved to: {output_file}")
print("=" * 70)
