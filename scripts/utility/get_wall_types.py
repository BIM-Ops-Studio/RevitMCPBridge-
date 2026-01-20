"""Get available wall types from Revit"""
import win32file
import json

pipe = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None, win32file.OPEN_EXISTING, 0, None
)

request = json.dumps({'method': 'getWallTypes', 'params': {}}) + '\n'
win32file.WriteFile(pipe, request.encode())

# Read in chunks until we get complete JSON
chunks = []
while True:
    result, data = win32file.ReadFile(pipe, 65536)
    chunks.append(data)
    # Check if we have complete JSON (ends with } or ])
    combined = b''.join(chunks).decode()
    if combined.strip().endswith('}') or combined.strip().endswith(']'):
        break
    if len(data) < 1024:  # No more data
        break

win32file.CloseHandle(pipe)

raw = b''.join(chunks).decode().strip()
print(f"Response length: {len(raw)} bytes")
print(f"First 500 chars: {raw[:500]}")
print(f"Last 200 chars: {raw[-200:]}")

try:
    response = json.loads(raw)
    if response.get('success'):
        print("\nAVAILABLE WALL TYPES:")
        print("=" * 60)
        for wt in response.get('wallTypes', [])[:20]:  # First 20
            name = wt.get('name', 'Unknown')
            wt_id = wt.get('wallTypeId', 0)
            width = wt.get('width', 0)
            width_in = width * 12 if width else 0
            print(f"ID: {wt_id:8} | {width_in:5.1f}\" | {name}")
    else:
        print("Error:", response.get('error'))
except Exception as e:
    print(f"Parse error: {e}")
