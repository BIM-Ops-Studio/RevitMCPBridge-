"""
Extract Doors and Windows from Original Model
Gets positions for reproduction
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
print("EXTRACTING DOORS AND WINDOWS")
print("=" * 70)

# Get Doors
print("\n[1] Getting Doors...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"Found {len(doors)} doors")

door_data = []
for door in doors:
    door_id = door.get("id")
    # Try to get more info
    try:
        info = call_mcp("getElementInfo", {"elementId": door_id})
        if info.get("success"):
            door_data.append({
                "id": door_id,
                "name": door.get("name"),
                "typename": door.get("typename"),
                "level": door.get("level"),
                "location": info.get("location"),
                "hostId": info.get("hostId"),
            })
        else:
            door_data.append({
                "id": door_id,
                "name": door.get("name"),
                "typename": door.get("typename"),
                "level": door.get("level"),
            })
    except:
        door_data.append({
            "id": door_id,
            "name": door.get("name"),
            "level": door.get("level"),
        })

print("\nDoors found:")
for d in door_data:
    name = d.get("name", "Unknown")
    level = d.get("level", "?")
    loc = d.get("location")
    if loc:
        print(f"  {name} at ({loc[0]:.2f}, {loc[1]:.2f}) - {level}")
    else:
        print(f"  {name} - {level}")

# Get Windows
print("\n[2] Getting Windows...")
r = call_mcp("getElements", {"category": "Windows"})
windows = r.get("result", {}).get("elements", [])
print(f"Found {len(windows)} windows")

window_data = []
for window in windows:
    win_id = window.get("id")
    try:
        info = call_mcp("getElementInfo", {"elementId": win_id})
        if info.get("success"):
            window_data.append({
                "id": win_id,
                "name": window.get("name"),
                "typename": window.get("typename"),
                "level": window.get("level"),
                "location": info.get("location"),
                "hostId": info.get("hostId"),
            })
        else:
            window_data.append({
                "id": win_id,
                "name": window.get("name"),
                "typename": window.get("typename"),
                "level": window.get("level"),
            })
    except:
        window_data.append({
            "id": win_id,
            "name": window.get("name"),
            "level": window.get("level"),
        })

print("\nWindows found:")
for w in window_data:
    name = w.get("name", "Unknown")
    level = w.get("level", "?")
    loc = w.get("location")
    if loc:
        print(f"  {name} at ({loc[0]:.2f}, {loc[1]:.2f}) - {level}")
    else:
        print(f"  {name} - {level}")

# Get Openings
print("\n[3] Getting Openings...")
r = call_mcp("getElements", {"category": "Openings"})
openings = r.get("result", {}).get("elements", [])
print(f"Found {len(openings)} openings")

# Save all data
output = {
    "doors": door_data,
    "windows": window_data,
    "openings": openings
}

output_file = "d:/RevitMCPBridge2026/doors_windows_data.json"
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print(f"Data saved to: {output_file}")
print("=" * 70)
print(f"""
Summary:
  Doors: {len(door_data)}
  Windows: {len(window_data)}
  Openings: {len(openings)}
""")
