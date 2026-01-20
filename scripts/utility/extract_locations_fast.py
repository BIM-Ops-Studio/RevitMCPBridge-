"""
Fast extraction of element locations only (skips slow getParameters)
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
print("FAST EXTRACTION - LOCATIONS ONLY", flush=True)
print("=" * 70, flush=True)

all_data = {}

categories = [
    ("Casework", "Casework"),
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Furniture", "Furniture"),
]

# Get family types
print("\n[1] FAMILY TYPES", flush=True)
for display_name, category in categories:
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        all_data[f"{category}_types"] = types
        print(f"  {display_name}: {len(types)} types", flush=True)

# Get element locations
print("\n[2] ELEMENT LOCATIONS", flush=True)
for display_name, category in categories:
    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    print(f"\n{display_name}: {len(elements)} elements", flush=True)

    category_data = []
    for elem in elements:
        elem_id = elem.get("id")

        # Get location only
        loc_r = call_mcp("getElementLocation", {"elementId": elem_id})

        elem_data = {"id": elem_id, "location": None, "rotation": 0}

        if loc_r.get("success"):
            loc_type = loc_r.get("locationType")
            if loc_type == "Point":
                elem_data["location"] = loc_r.get("point")
                elem_data["rotation"] = loc_r.get("rotation", 0)
            elif loc_type == "BoundingBoxCenter":
                elem_data["location"] = loc_r.get("point")

        category_data.append(elem_data)

    all_data[category] = category_data

    # Show results
    for item in category_data[:3]:
        loc = item.get("location", [0,0,0])
        if loc:
            print(f"  ID {item['id']}: ({loc[0]:.1f}, {loc[1]:.1f}) rot={item['rotation']:.0f}°", flush=True)
    if len(category_data) > 3:
        print(f"  ... and {len(category_data) - 3} more", flush=True)

# Save
output_file = "D:\\RevitMCPBridge2026\\element_locations.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"\n\nSaved to: {output_file}", flush=True)

# Summary
print("\nSUMMARY:", flush=True)
for cat in ["Casework", "Plumbing Fixtures", "Furniture"]:
    items = all_data.get(cat, [])
    types = all_data.get(f"{cat}_types", [])
    print(f"  {cat}: {len(items)} elements, {len(types)} types", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
