"""
Extract All Wall Geometry - Using correct getWallInfo method
Gets start/end coordinates for all 58 walls
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
print("EXTRACTING ALL WALL GEOMETRY")
print("=" * 70)

# Get wall list first
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"\nFound {len(walls)} walls")

# Get detailed info for each wall using getWallInfo
wall_data = []

print("\nExtracting wall coordinates...")

for i, wall in enumerate(walls):
    wall_id = wall.get("id")

    try:
        r = call_mcp("getWallInfo", {"wallId": wall_id})
        if r.get("success"):
            wall_info = {
                "id": wall_id,
                "name": r.get("wallType"),
                "level": r.get("level"),
                "startPoint": r.get("startPoint"),
                "endPoint": r.get("endPoint"),
                "length": r.get("length"),
                "height": r.get("height"),
                "width": r.get("width"),
            }
            wall_data.append(wall_info)

            # Show progress
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(walls)} walls...")
        else:
            print(f"  Wall {wall_id}: {r.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  Wall {wall_id}: Error - {e}")

print(f"\nGot geometry for {len(wall_data)} walls")

# Organize by wall type
exterior_walls = [w for w in wall_data if "CMU Exterior" in w.get("name", "") or "W1" in w.get("name", "")]
interior_walls = [w for w in wall_data if "Partition" in w.get("name", "") or "Interior" in w.get("name", "")]
foundation_walls = [w for w in wall_data if "Foundation" in w.get("name", "")]
other_walls = [w for w in wall_data if w not in exterior_walls and w not in interior_walls and w not in foundation_walls]

# Display exterior walls
print("\n" + "=" * 70)
print(f"EXTERIOR WALLS ({len(exterior_walls)} walls):")
print("=" * 70)

for w in exterior_walls:
    sp = w.get("startPoint", [0,0,0])
    ep = w.get("endPoint", [0,0,0])
    length = w.get("length", 0)
    name = w.get("name", "Unknown")
    level = w.get("level", "?")
    print(f"  [{level}] {name}")
    print(f"    ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  L={length:.2f}'")

# Display interior walls
print("\n" + "=" * 70)
print(f"INTERIOR WALLS ({len(interior_walls)} walls):")
print("=" * 70)

for w in interior_walls:
    sp = w.get("startPoint", [0,0,0])
    ep = w.get("endPoint", [0,0,0])
    length = w.get("length", 0)
    name = w.get("name", "Unknown")
    level = w.get("level", "?")
    print(f"  [{level}] {name}")
    print(f"    ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  L={length:.2f}'")

# Display foundation walls
if foundation_walls:
    print("\n" + "=" * 70)
    print(f"FOUNDATION WALLS ({len(foundation_walls)} walls):")
    print("=" * 70)

    for w in foundation_walls:
        sp = w.get("startPoint", [0,0,0])
        ep = w.get("endPoint", [0,0,0])
        length = w.get("length", 0)
        name = w.get("name", "Unknown")
        level = w.get("level", "?")
        print(f"  [{level}] {name}")
        print(f"    ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  L={length:.2f}'")

# Display other walls
if other_walls:
    print("\n" + "=" * 70)
    print(f"OTHER WALLS ({len(other_walls)} walls):")
    print("=" * 70)

    for w in other_walls:
        sp = w.get("startPoint", [0,0,0])
        ep = w.get("endPoint", [0,0,0])
        length = w.get("length", 0)
        name = w.get("name", "Unknown")
        level = w.get("level", "?")
        print(f"  [{level}] {name}")
        print(f"    ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f})  L={length:.2f}'")

# Save all data
output_file = "d:/RevitMCPBridge2026/all_walls_geometry.json"
with open(output_file, 'w') as f:
    json.dump({
        "total": len(wall_data),
        "exterior": exterior_walls,
        "interior": interior_walls,
        "foundation": foundation_walls,
        "other": other_walls
    }, f, indent=2)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print(f"Complete wall data saved to: {output_file}")
print("=" * 70)

# Summary
print(f"""
SUMMARY:
- Total walls: {len(wall_data)}
- Exterior: {len(exterior_walls)}
- Interior: {len(interior_walls)}
- Foundation: {len(foundation_walls)}
- Other: {len(other_walls)}
""")
