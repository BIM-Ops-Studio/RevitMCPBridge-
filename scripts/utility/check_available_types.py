"""
Check Available Door and Window Types in New Model
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
print("CHECKING AVAILABLE DOOR/WINDOW TYPES")
print("=" * 70)

# Get door types
print("\n[1] Door Types Available:")
r = call_mcp("getDoorTypes", {})
if r.get("success"):
    door_types = r.get("doorTypes", [])
    print(f"Found {len(door_types)} door types\n")
    for dt in door_types:
        print(f"  {dt.get('familyName')} - {dt.get('typeName')}")
        print(f"    TypeID: {dt.get('typeId')}")
else:
    print(f"  Error: {r.get('error')}")

# Get window types
print("\n\n[2] Window Types Available:")
r = call_mcp("getWindowTypes", {})
if r.get("success"):
    window_types = r.get("windowTypes", [])
    print(f"Found {len(window_types)} window types\n")
    for wt in window_types:
        print(f"  {wt.get('familyName')} - {wt.get('typeName')}")
        print(f"    TypeID: {wt.get('typeId')}")
else:
    print(f"  Error: {r.get('error')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
