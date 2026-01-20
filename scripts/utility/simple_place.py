"""
Simple Placement - Place elements one at a time without pre-fetching walls
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
print("SIMPLE PLACEMENT TEST")
print("=" * 60)

# Test connection
print("\nTesting connection...")
r = call_mcp("getLevels", {})
print(f"Levels: {len(r.get('levels', []))}")

# Get first wall to use as host
print("\nGetting walls...")
r = call_mcp("getElements", {"category": "Walls"})
walls = r.get("result", {}).get("elements", [])
print(f"Found {len(walls)} walls")

if not walls:
    print("No walls found!")
    exit(1)

# Use first exterior wall
first_wall = walls[0]["id"]
print(f"Using first wall ID: {first_wall}")

# Place one test door
print("\nPlacing test door...")
r = call_mcp("placeDoor", {
    "wallId": first_wall,
    "doorTypeId": 387958  # 36" x 80" Door-Passage-Single-Flush
})
print(f"Result: {r}")

win32file.CloseHandle(pipe)
print("\nDone!")
