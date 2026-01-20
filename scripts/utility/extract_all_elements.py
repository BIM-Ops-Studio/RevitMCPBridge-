"""
Extract detailed location and type data for all elements to transfer:
- Casework, Plumbing Fixtures, Furniture (point-based)
- Ceilings, Roofs, Floors (sketch-based)
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
print("EXTRACTING ALL ELEMENT DATA FROM ORIGINAL MODEL")
print("=" * 70)

all_data = {}

# Categories to extract with point locations
point_categories = [
    ("Casework", "Casework"),
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Furniture", "Furniture"),
]

# Categories that are sketch-based
sketch_categories = [
    ("Ceilings", "Ceilings"),
    ("Roofs", "Roofs"),
    ("Floors", "Floors"),
]

# Extract point-based elements (casework, fixtures, furniture)
for display_name, category in point_categories:
    print(f"\n{'='*70}")
    print(f"EXTRACTING {display_name.upper()}")
    print("=" * 70)

    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    print(f"Found {len(elements)} {display_name.lower()}")

    category_data = []

    for elem in elements:
        elem_id = elem.get("id")

        # Get element location using getBoundingBox
        bbox_r = call_mcp("getBoundingBox", {"elementId": elem_id})

        # Get parameters for family/type info
        family_name = ""
        type_name = ""
        level_name = ""

        try:
            params_r = call_mcp("getParameters", {"elementId": elem_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                for p in params:
                    name = p.get("name", "")
                    value = p.get("value", "")
                    if name == "Family":
                        family_name = value
                    elif name == "Type":
                        type_name = value
                    elif name == "Family and Type":
                        parts = value.split(":")
                        if len(parts) >= 2:
                            family_name = parts[0].strip()
                            type_name = parts[1].strip()
                    elif name == "Level":
                        level_name = value
        except:
            pass

        # Calculate center point from bounding box
        location = [0, 0, 0]
        if bbox_r.get("success"):
            min_pt = bbox_r.get("min", [0, 0, 0])
            max_pt = bbox_r.get("max", [0, 0, 0])
            location = [
                (min_pt[0] + max_pt[0]) / 2,
                (min_pt[1] + max_pt[1]) / 2,
                (min_pt[2] + max_pt[2]) / 2
            ]

        elem_data = {
            "id": elem_id,
            "family": family_name,
            "type": type_name,
            "level": level_name,
            "location": location
        }
        category_data.append(elem_data)

        # Display
        display_type = f"{family_name} - {type_name}" if family_name else f"ID {elem_id}"
        print(f"  {display_type[:50]}")
        print(f"    Location: ({location[0]:.2f}, {location[1]:.2f}, {location[2]:.2f})")

    all_data[category] = category_data

# Extract sketch-based elements (get basic info)
for display_name, category in sketch_categories:
    print(f"\n{'='*70}")
    print(f"EXTRACTING {display_name.upper()}")
    print("=" * 70)

    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    print(f"Found {len(elements)} {display_name.lower()}")

    category_data = []

    for elem in elements:
        elem_id = elem.get("id")

        # Get bounding box for approximate location
        bbox_r = call_mcp("getBoundingBox", {"elementId": elem_id})

        # Get type info
        type_name = ""
        level_name = ""

        try:
            params_r = call_mcp("getParameters", {"elementId": elem_id})
            if params_r.get("success"):
                params = params_r.get("parameters", [])
                for p in params:
                    name = p.get("name", "")
                    value = p.get("value", "")
                    if name == "Type":
                        type_name = value
                    elif name == "Level":
                        level_name = value
        except:
            pass

        # Get bounds
        bounds = None
        if bbox_r.get("success"):
            bounds = {
                "min": bbox_r.get("min", [0, 0, 0]),
                "max": bbox_r.get("max", [0, 0, 0])
            }

        elem_data = {
            "id": elem_id,
            "type": type_name,
            "level": level_name,
            "bounds": bounds
        }
        category_data.append(elem_data)

        # Display
        if bounds:
            min_pt = bounds["min"]
            max_pt = bounds["max"]
            print(f"  ID {elem_id}: {type_name}")
            print(f"    Level: {level_name}")
            print(f"    Bounds: ({min_pt[0]:.1f}, {min_pt[1]:.1f}) to ({max_pt[0]:.1f}, {max_pt[1]:.1f})")
        else:
            print(f"  ID {elem_id}: {type_name}")

    all_data[category] = category_data

# Save to JSON file
output_file = "D:\\RevitMCPBridge2026\\original_elements_data.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"\n\n{'='*70}")
print("DATA SAVED TO: original_elements_data.json")
print("=" * 70)

# Summary
print("\nSUMMARY:")
for cat, items in all_data.items():
    print(f"  {cat}: {len(items)} elements")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)
