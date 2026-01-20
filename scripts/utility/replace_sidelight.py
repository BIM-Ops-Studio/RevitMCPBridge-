"""
Replace window mark 124 with correct sidelight type
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
print("REPLACING SIDELIGHT WINDOW")
print("=" * 60)

# Get all windows
print("\n[1] Finding all windows...")
r = call_mcp("getElements", {"category": "Windows"})
windows = r.get("result", {}).get("elements", [])
print(f"Found {len(windows)} windows")

# Find the sidelight window (it was placed at location (4.84, -13.16))
print("\n[2] Looking for sidelight window...")
sidelight_loc = (4.8, -13.2)  # Approximate location
target_window = None

for win in windows:
    win_id = win.get("id")
    info = call_mcp("getDoorWindowInfo", {"elementId": win_id})
    if info.get("success"):
        loc = info.get("location", [0, 0, 0])
        # Check if this is near the sidelight location
        if abs(loc[0] - sidelight_loc[0]) < 1 and abs(loc[1] - sidelight_loc[1]) < 1:
            target_window = {
                "id": win_id,
                "family": info.get("familyName"),
                "type": info.get("typeName"),
                "typeId": info.get("typeId"),
                "hostId": info.get("hostId"),
                "location": loc
            }
            print(f"  Found: {info.get('familyName')} - {info.get('typeName')}")
            print(f"    ID: {win_id}")
            print(f"    Location: ({loc[0]:.2f}, {loc[1]:.2f})")
            print(f"    Host Wall: {info.get('hostId')}")
            break

if not target_window:
    print("  Sidelight window not found at expected location")

# Get available window types to find sidelight options
print("\n[3] Available window types with 'sidelight' or 'side':")
r = call_mcp("getWindowTypes", {})
sidelight_types = []

if r.get("success"):
    window_types = r.get("windowTypes", [])
    for wt in window_types:
        family = wt.get("familyName", "").lower()
        type_name = wt.get("typeName", "").lower()
        if "side" in family or "side" in type_name or "light" in family or "entry" in family:
            sidelight_types.append(wt)
            print(f"  {wt.get('familyName')} - {wt.get('typeName')}")
            print(f"    TypeID: {wt.get('typeId')}")

    # Also show all window types for reference
    print(f"\n  Total window types available: {len(window_types)}")

# If we found the window and have sidelight types, show options
if target_window and sidelight_types:
    print("\n[4] To replace, use one of these sidelight type IDs:")
    for st in sidelight_types:
        print(f"  {st.get('typeId')}: {st.get('familyName')} - {st.get('typeName')}")

# Let's also check all window types in case sidelight has different name
print("\n\n[5] ALL WINDOW TYPES (for reference):")
if r.get("success"):
    for wt in window_types:
        print(f"  {wt.get('typeId')}: {wt.get('familyName')} - {wt.get('typeName')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
