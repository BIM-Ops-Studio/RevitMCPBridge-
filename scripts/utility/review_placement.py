"""
Review what was placed in the new model
"""
import win32file
import json
import sys

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

print("=" * 70, flush=True)
print("REVIEWING PLACED ELEMENTS IN NEW MODEL", flush=True)
print("=" * 70, flush=True)

categories = ["Casework", "Plumbing Fixtures", "Furniture"]

for category in categories:
    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])

    print(f"\n{'='*70}", flush=True)
    print(f"{category.upper()}: {len(elements)} elements", flush=True)
    print("=" * 70, flush=True)

    for i, elem in enumerate(elements):
        elem_id = elem.get("id")
        elem_name = elem.get("name", "Unknown")

        # Get location
        loc_r = call_mcp("getElementLocation", {"elementId": elem_id})

        if loc_r.get("success"):
            loc = loc_r.get("point", [0, 0, 0])
            rot = loc_r.get("rotation", 0)
            print(f"  [{i+1}] {elem_name}", flush=True)
            print(f"       ID: {elem_id}", flush=True)
            print(f"       Location: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})", flush=True)
            print(f"       Rotation: {rot:.1f} deg", flush=True)
        else:
            print(f"  [{i+1}] {elem_name} - Could not get location", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
