"""
Analyze Active Revit Model
Extract all data for learning and reproduction
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

print("=" * 70)
print("ANALYZING ACTIVE REVIT MODEL")
print("Extracting all data for learning")
print("=" * 70)

# Collect all data
model_data = {
    "levels": [],
    "walls": [],
    "rooms": [],
    "floors": [],
    "doors": [],
    "windows": [],
}

# 1. Get Levels
print("\n[1/6] Getting Levels...")
r = call_mcp("getLevels", {})
if r.get("levels"):
    model_data["levels"] = r["levels"]
    for lvl in r["levels"]:
        print(f"  - {lvl.get('name')}: ID={lvl.get('levelId')}, Elevation={lvl.get('elevation')}")

# 2. Get Walls
print("\n[2/6] Getting Walls...")
r = call_mcp("getWalls", {})
if r.get("walls"):
    model_data["walls"] = r["walls"]
    print(f"  Found {len(r['walls'])} walls")
    for i, wall in enumerate(r["walls"][:5]):  # Show first 5
        print(f"  - Wall {i+1}: Type={wall.get('wallType')}, Length={wall.get('length')}")
    if len(r["walls"]) > 5:
        print(f"  ... and {len(r['walls'])-5} more")

# 3. Get Rooms
print("\n[3/6] Getting Rooms...")
r = call_mcp("getRooms", {})
if r.get("rooms"):
    model_data["rooms"] = r["rooms"]
    print(f"  Found {len(r['rooms'])} rooms")
    for room in r["rooms"]:
        print(f"  - {room.get('name')}: Area={room.get('area')}")

# 4. Get Floors
print("\n[4/6] Getting Floors...")
r = call_mcp("getFloors", {})
if r.get("floors"):
    model_data["floors"] = r["floors"]
    print(f"  Found {len(r['floors'])} floors")

# 5. Get Doors
print("\n[5/6] Getting Doors...")
r = call_mcp("getDoors", {})
if r.get("doors"):
    model_data["doors"] = r["doors"]
    print(f"  Found {len(r['doors'])} doors")

# 6. Get Windows
print("\n[6/6] Getting Windows...")
r = call_mcp("getWindows", {})
if r.get("windows"):
    model_data["windows"] = r["windows"]
    print(f"  Found {len(r['windows'])} windows")

# Save to JSON for detailed analysis
output_file = "d:/RevitMCPBridge2026/model_analysis.json"
with open(output_file, 'w') as f:
    json.dump(model_data, f, indent=2)
print(f"\n\nFull data saved to: {output_file}")

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"""
Summary:
- Levels: {len(model_data['levels'])}
- Walls: {len(model_data['walls'])}
- Rooms: {len(model_data['rooms'])}
- Floors: {len(model_data['floors'])}
- Doors: {len(model_data['doors'])}
- Windows: {len(model_data['windows'])}

Full data saved to model_analysis.json
""")
