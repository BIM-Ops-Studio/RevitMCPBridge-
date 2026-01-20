"""
Extract casework locations from original model
"""
import win32file
import json
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

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

print("=" * 60, flush=True)
print("EXTRACTING CASEWORK FROM ORIGINAL MODEL", flush=True)
print("=" * 60, flush=True)

# Get casework elements
r = call_mcp("getElements", {"category": "Casework"})
elements = r.get("result", {}).get("elements", [])
print(f"Found {len(elements)} casework elements", flush=True)

casework_data = []

for i, elem in enumerate(elements):
    elem_id = elem.get("id")
    print(f"  Processing {i+1}/{len(elements)}: ID {elem_id}...", flush=True)

    # Get bounding box for location
    bbox_r = call_mcp("getBoundingBox", {"elementId": elem_id})

    location = [0, 0, 0]
    if bbox_r.get("success"):
        min_pt = bbox_r.get("min", [0, 0, 0])
        max_pt = bbox_r.get("max", [0, 0, 0])
        location = [
            (min_pt[0] + max_pt[0]) / 2,
            (min_pt[1] + max_pt[1]) / 2,
            min_pt[2]  # Use base Z
        ]

    casework_data.append({
        "id": elem_id,
        "location": location
    })

# Save data
with open("D:\\RevitMCPBridge2026\\casework_data.json", 'w') as f:
    json.dump(casework_data, f, indent=2)

print(f"\nExtracted {len(casework_data)} casework items", flush=True)
print("Saved to casework_data.json", flush=True)

# Show summary
print("\nCasework locations:", flush=True)
for item in casework_data:
    loc = item["location"]
    print(f"  ID {item['id']}: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f})", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
