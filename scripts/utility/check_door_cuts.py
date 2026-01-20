"""
Investigate why doors aren't cutting walls
Check door properties and wall function
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
print("INVESTIGATING DOOR WALL CUTS")
print("=" * 60)

# Get all doors
print("\nGetting all doors...")
r = call_mcp("getElements", {"category": "Doors"})
doors = r.get("result", {}).get("elements", [])
print(f"Found {len(doors)} doors")

# Check properties of first few doors
print("\n[1] Checking Door Properties:")
for i, door in enumerate(doors[:5]):
    door_id = door.get("id")
    print(f"\n  Door {i+1} (ID: {door_id}):")

    # Get detailed info
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        print(f"    Family: {info.get('familyName')}")
        print(f"    Type: {info.get('typeName')}")
        print(f"    Host Wall: {info.get('hostId')}")
        print(f"    Width: {info.get('width')}")
        print(f"    Height: {info.get('height')}")

        # Get parameters
        params_r = call_mcp("getParameters", {"elementId": door_id})
        if params_r.get("success"):
            params = params_r.get("parameters", [])

            # Look for key parameters
            for p in params:
                name = p.get("name", "")
                if any(key in name.lower() for key in ["sill", "cut", "function", "wall"]):
                    print(f"    {name}: {p.get('value')}")

# Check walls that host doors
print("\n\n[2] Checking Host Wall Properties:")
checked_walls = set()
for door in doors[:5]:
    door_id = door.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
    if info.get("success"):
        host_id = info.get("hostId")
        if host_id and host_id not in checked_walls:
            checked_walls.add(host_id)
            print(f"\n  Wall ID: {host_id}")

            # Get wall parameters
            params_r = call_mcp("getParameters", {"elementId": host_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                for p in params:
                    name = p.get("name", "")
                    if any(key in name.lower() for key in ["function", "structural", "room"]):
                        print(f"    {name}: {p.get('value')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("POSSIBLE CAUSES:")
print("=" * 60)
print("""
1. Door Sill Height - Should be 0 for floor-level doors
2. Wall Function - Must allow cuts for doors
3. Door family 'Cuts Wall' property - Must be enabled
4. Join geometry issues - May need manual join/unjoin

Try in Revit:
- Select a door that isn't cutting
- Check Properties > Sill Height (should be 0' - 0")
- Check if door family has "Cuts Wall" parameter
- Try: Modify tab > Geometry > Cut (select door, then wall)
""")
