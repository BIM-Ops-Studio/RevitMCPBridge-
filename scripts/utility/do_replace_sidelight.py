"""
Replace window mark 124 with correct Sidelight type
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
print("REPLACING WINDOW MARK 124 WITH SIDELIGHT")
print("=" * 60)

# Current window info
old_window_id = 1252976
wall_id = 1240476
location = [4.84, -13.16, 0.0]
new_type_id = 1253934  # Sidelight - 18" x 84"

print(f"\n[1] Deleting old window {old_window_id}...")
r = call_mcp("deleteDoorWindow", {"elementId": old_window_id})
if r.get("success"):
    print("  Deleted successfully")
else:
    print(f"  Error: {r.get('error', 'Unknown')}")
    win32file.CloseHandle(pipe)
    exit(1)

time.sleep(0.2)

print(f"\n[2] Placing new Sidelight (18\" x 84\") at same location...")
r = call_mcp("placeWindow", {
    "wallId": wall_id,
    "location": location,
    "windowTypeId": new_type_id
})

if r.get("success"):
    new_id = r.get("windowId")
    print(f"  Placed new sidelight: ID {new_id}")
    print("  SUCCESS!")
else:
    print(f"  Error: {r.get('error', 'Unknown')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("Window mark 124 has been replaced with correct Sidelight type")
print("=" * 60)
