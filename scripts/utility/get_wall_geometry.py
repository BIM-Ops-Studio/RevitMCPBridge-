"""
Get Wall Geometry - Extract coordinates for all walls
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
print("EXTRACTING WALL GEOMETRY")
print("=" * 70)

# Get wall list first
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"\nFound {len(walls)} walls")

# Try to get geometry for each wall
wall_data = []

# Try getWallLocation method
print("\nTrying to get wall locations...")

for wall in walls:
    wall_id = wall.get("id")
    wall_name = wall.get("name")
    wall_level = wall.get("level")

    # Try getWallLocation
    try:
        r = call_mcp("getWallLocation", {"wallId": wall_id})
        if r.get("success"):
            wall_info = {
                "id": wall_id,
                "name": wall_name,
                "level": wall_level,
                "startPoint": r.get("startPoint"),
                "endPoint": r.get("endPoint"),
                "length": r.get("length"),
                "height": r.get("height"),
            }
            wall_data.append(wall_info)
    except Exception as e:
        pass

print(f"\nGot geometry for {len(wall_data)} walls")

# Show exterior walls (F.F. level, CMU type)
print("\n" + "=" * 70)
print("EXTERIOR WALLS (8\" CMU on F.F. level):")
print("=" * 70)

exterior_walls = [w for w in wall_data if "CMU Exterior" in w.get("name", "") and w.get("level") == "F.F."]
for w in exterior_walls:
    sp = w.get("startPoint", [0,0,0])
    ep = w.get("endPoint", [0,0,0])
    length = w.get("length", 0)
    print(f"  ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  Length: {length:.2f}'")

# Show interior walls
print("\n" + "=" * 70)
print("INTERIOR WALLS (4 1/2\" Partition on F.F. level):")
print("=" * 70)

interior_walls = [w for w in wall_data if "Partition" in w.get("name", "") and w.get("level") == "F.F."]
for w in interior_walls[:10]:  # Show first 10
    sp = w.get("startPoint", [0,0,0])
    ep = w.get("endPoint", [0,0,0])
    length = w.get("length", 0)
    print(f"  ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  Length: {length:.2f}'")

if len(interior_walls) > 10:
    print(f"  ... and {len(interior_walls)-10} more")

# Save all data
output_file = "d:/RevitMCPBridge2026/wall_geometry.json"
with open(output_file, 'w') as f:
    json.dump(wall_data, f, indent=2)

win32file.CloseHandle(pipe)

print(f"\n\nFull wall geometry saved to: {output_file}")
