"""
Extract element data WITH family/type names for accurate placement
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
print("EXTRACTING ELEMENTS WITH TYPE INFORMATION", flush=True)
print("=" * 70, flush=True)

all_data = {}

categories = [
    ("Casework", "Casework"),
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Furniture", "Furniture"),
]

# Get family types available
print("\n[1] AVAILABLE FAMILY TYPES", flush=True)
for display_name, category in categories:
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        all_data[f"{category}_types"] = types
        print(f"  {display_name}: {len(types)} types", flush=True)

# Get elements with their type info
print("\n[2] EXTRACTING ELEMENTS WITH TYPES", flush=True)
for display_name, category in categories:
    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    print(f"\n{display_name}: {len(elements)} elements", flush=True)

    category_data = []

    for i, elem in enumerate(elements):
        elem_id = elem.get("id")
        elem_name = elem.get("name", "Unknown")

        # Get location
        loc_r = call_mcp("getElementLocation", {"elementId": elem_id})

        elem_data = {
            "id": elem_id,
            "name": elem_name,
            "location": None,
            "rotation": 0,
            "family": None,
            "type": None,
            "typeId": None
        }

        if loc_r.get("success"):
            loc_type = loc_r.get("locationType")
            if loc_type == "Point":
                elem_data["location"] = loc_r.get("point")
                elem_data["rotation"] = loc_r.get("rotation", 0)
            elif loc_type == "BoundingBoxCenter":
                elem_data["location"] = loc_r.get("point")

        # Parse family and type from name (format: "Family : Type")
        if " : " in elem_name:
            parts = elem_name.split(" : ")
            elem_data["family"] = parts[0].strip()
            elem_data["type"] = parts[1].strip() if len(parts) > 1 else None
        else:
            elem_data["family"] = elem_name

        # Try to find matching typeId from available types
        if elem_data["family"] and elem_data["type"]:
            full_name = f"{elem_data['family']} - {elem_data['type']}"
            for t in all_data.get(f"{category}_types", []):
                if t.get("fullName") == full_name:
                    elem_data["typeId"] = t.get("typeId")
                    break

        category_data.append(elem_data)

        # Show each element
        loc = elem_data.get("location", [0, 0, 0])
        if loc:
            print(f"  [{i+1}] {elem_data['family']} - {elem_data['type']}", flush=True)
            print(f"       Loc: ({loc[0]:.1f}, {loc[1]:.1f}) Rot: {elem_data['rotation']:.0f}°", flush=True)

    all_data[category] = category_data

# Save
output_file = "D:\\RevitMCPBridge2026\\elements_with_types.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"\n\nSaved to: {output_file}", flush=True)

# Summary
print("\n" + "=" * 70, flush=True)
print("SUMMARY", flush=True)
print("=" * 70, flush=True)
for cat in ["Casework", "Plumbing Fixtures", "Furniture"]:
    items = all_data.get(cat, [])
    print(f"\n{cat}: {len(items)} elements", flush=True)

    # Count by family type
    type_counts = {}
    for item in items:
        key = f"{item.get('family', 'Unknown')} - {item.get('type', 'Unknown')}"
        type_counts[key] = type_counts.get(key, 0) + 1

    for type_name, count in sorted(type_counts.items()):
        print(f"  {count}x {type_name}", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
