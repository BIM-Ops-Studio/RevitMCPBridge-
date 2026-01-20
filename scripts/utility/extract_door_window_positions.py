"""
Extract Door and Window Positions with Host Wall Info
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
print("EXTRACTING DOOR AND WINDOW POSITIONS")
print("=" * 70)

# Get Doors
print("\n[1] Getting Door Positions...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])

door_data = []
for door in doors:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        door_data.append({
            "id": door_id,
            "typeName": info.get("typeName"),
            "typeId": info.get("typeId"),
            "familyName": info.get("familyName"),
            "hostId": info.get("hostId"),
            "location": info.get("location"),
            "width": info.get("width"),
            "height": info.get("height"),
            "level": info.get("level"),
        })

print(f"Got positions for {len(door_data)} doors\n")

print("DOORS:")
print("-" * 70)
for d in door_data:
    loc = d.get("location", [0,0,0])
    width = d.get("width", 0) * 12  # Convert to inches
    height = d.get("height", 0) * 12
    name = d.get("typeName", "Unknown")
    host = d.get("hostId", -1)
    print(f"  {name}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print(f"    Size: {width:.0f}\" x {height:.0f}\"")
    print(f"    Host Wall ID: {host}")
    print()

# Get Windows
print("\n[2] Getting Window Positions...")
r = call_mcp("getElements", {"category": "Windows"})
windows = r.get("result", {}).get("elements", [])

window_data = []
for window in windows:
    win_id = window.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": win_id})
    if info.get("success"):
        window_data.append({
            "id": win_id,
            "typeName": info.get("typeName"),
            "typeId": info.get("typeId"),
            "familyName": info.get("familyName"),
            "hostId": info.get("hostId"),
            "location": info.get("location"),
            "width": info.get("width"),
            "height": info.get("height"),
            "level": info.get("level"),
        })

print(f"Got positions for {len(window_data)} windows\n")

print("WINDOWS:")
print("-" * 70)
for w in window_data:
    loc = w.get("location", [0,0,0])
    width = w.get("width", 0) * 12
    height = w.get("height", 0) * 12
    name = w.get("typeName", "Unknown")
    host = w.get("hostId", -1)
    print(f"  {name}")
    print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
    print(f"    Size: {width:.0f}\" x {height:.0f}\"")
    print(f"    Host Wall ID: {host}")
    print()

# Save all data
output = {
    "doors": door_data,
    "windows": window_data
}

output_file = "d:/RevitMCPBridge2026/door_window_positions.json"
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

win32file.CloseHandle(pipe)

print("=" * 70)
print(f"Data saved to: {output_file}")
print("=" * 70)
print(f"""
SUMMARY:
  Doors: {len(door_data)}
  Windows: {len(window_data)}
""")
