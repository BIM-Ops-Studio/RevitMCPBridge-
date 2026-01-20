"""
Extract element data using new MCP methods:
- getElementLocation
- getBoundingBox
- getFamilyInstanceTypes
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
print("EXTRACTING ELEMENT DATA WITH NEW METHODS", flush=True)
print("=" * 70, flush=True)

all_data = {}

# Categories to extract
categories = [
    ("Casework", "Casework"),
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Furniture", "Furniture"),
]

# First, get available family types for each category
print("\n[1] GETTING AVAILABLE FAMILY TYPES", flush=True)
print("=" * 70, flush=True)

for display_name, category in categories:
    print(f"\n{display_name}:", flush=True)
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        print(f"  Found {len(types)} types", flush=True)
        for t in types[:5]:  # Show first 5
            print(f"    {t.get('typeId')}: {t.get('fullName')}", flush=True)
        if len(types) > 5:
            print(f"    ... and {len(types) - 5} more", flush=True)
        all_data[f"{category}_types"] = types
    else:
        print(f"  Error: {r.get('error')}", flush=True)

# Now extract element locations
print("\n\n[2] EXTRACTING ELEMENT LOCATIONS", flush=True)
print("=" * 70, flush=True)

for display_name, category in categories:
    print(f"\n{display_name}:", flush=True)

    # Get elements in category
    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    print(f"  Found {len(elements)} elements", flush=True)

    category_data = []

    for i, elem in enumerate(elements):
        elem_id = elem.get("id")

        # Get location using new method
        loc_r = call_mcp("getElementLocation", {"elementId": elem_id})

        elem_data = {
            "id": elem_id,
            "location": None,
            "rotation": 0
        }

        if loc_r.get("success"):
            loc_type = loc_r.get("locationType")
            if loc_type == "Point":
                elem_data["location"] = loc_r.get("point")
                elem_data["rotation"] = loc_r.get("rotation", 0)
            elif loc_type == "BoundingBoxCenter":
                elem_data["location"] = loc_r.get("point")
            elif loc_type == "Curve":
                # Use midpoint for curve-based elements
                start = loc_r.get("startPoint")
                end = loc_r.get("endPoint")
                elem_data["location"] = [
                    (start[0] + end[0]) / 2,
                    (start[1] + end[1]) / 2,
                    (start[2] + end[2]) / 2
                ]

        # Get parameters for type info
        try:
            params_r = call_mcp("getParameters", {"elementId": elem_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                for p in params:
                    name = p.get("name", "")
                    value = p.get("value", "")
                    if name == "Family and Type":
                        parts = value.split(":")
                        if len(parts) >= 2:
                            elem_data["family"] = parts[0].strip()
                            elem_data["type"] = parts[1].strip()
                    elif name == "Type" and "type" not in elem_data:
                        elem_data["type"] = value
                    elif name == "Family" and "family" not in elem_data:
                        elem_data["family"] = value
        except:
            pass

        category_data.append(elem_data)

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(elements)}...", flush=True)

    all_data[category] = category_data

    # Show summary
    print(f"  Extracted {len(category_data)} elements:", flush=True)
    for item in category_data[:3]:
        loc = item.get("location", [0, 0, 0])
        if loc:
            family = item.get("family", "Unknown")[:30]
            print(f"    {family}: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f})", flush=True)
    if len(category_data) > 3:
        print(f"    ... and {len(category_data) - 3} more", flush=True)

# Save to JSON
output_file = "D:\\RevitMCPBridge2026\\original_elements_complete.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"\n\nData saved to: {output_file}", flush=True)

# Summary
print("\n" + "=" * 70, flush=True)
print("EXTRACTION SUMMARY", flush=True)
print("=" * 70, flush=True)
for category in ["Casework", "Plumbing Fixtures", "Furniture"]:
    items = all_data.get(category, [])
    types = all_data.get(f"{category}_types", [])
    print(f"  {category}: {len(items)} elements, {len(types)} types available", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
