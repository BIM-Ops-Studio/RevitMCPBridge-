"""
Analyze Active Revit Model - Version 2
Try multiple methods to extract data
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
print("ANALYZING ACTIVE REVIT MODEL - v2")
print("Trying multiple query methods")
print("=" * 70)

all_data = {}

# Try various methods
methods_to_try = [
    ("getLevels", {}),
    ("getWalls", {}),
    ("getRooms", {}),
    ("getFloors", {}),
    ("getDoors", {}),
    ("getWindows", {}),
    ("getWallTypes", {}),
    ("getElements", {"category": "Walls"}),
    ("getElements", {"category": "Rooms"}),
    ("getProjectInfo", {}),
    ("getActiveView", {}),
]

for method, params in methods_to_try:
    try:
        print(f"\nTrying: {method}({params})...")
        r = call_mcp(method, params)
        all_data[method] = r

        # Print summary of response
        if isinstance(r, dict):
            for key, value in r.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                    # Show first item structure
                    if value and len(value) > 0:
                        print(f"    First item keys: {list(value[0].keys()) if isinstance(value[0], dict) else 'N/A'}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  Response: {str(r)[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

# Save all data
output_file = "d:/RevitMCPBridge2026/model_analysis_v2.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print(f"All data saved to: {output_file}")
print("=" * 70)
