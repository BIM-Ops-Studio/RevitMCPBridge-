"""
Analyze original model for elements to transfer:
- Ceilings, Roofs, Floors
- Door D10 (sliding door)
- Casework (cabinetry)
- Plumbing fixtures
- Furniture
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
print("ANALYZING ORIGINAL MODEL - ELEMENTS TO TRANSFER")
print("=" * 70)

# Categories to analyze
categories = [
    ("Ceilings", "Ceilings"),
    ("Roofs", "Roofs"),
    ("Floors", "Floors"),
    ("Casework", "Casework"),
    ("Plumbing Fixtures", "Plumbing Fixtures"),
    ("Furniture", "Furniture"),
    ("Doors", "Doors"),
]

results = {}

for display_name, category in categories:
    print(f"\n{'='*70}")
    print(f"{display_name.upper()}")
    print("=" * 70)

    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])
    results[category] = elements

    print(f"Found {len(elements)} {display_name.lower()}")

    if len(elements) == 0:
        continue

    # Get details for each element
    for elem in elements[:20]:  # Limit to first 20 for display
        elem_id = elem.get("id")

        # Get parameters to find type info
        params_r = call_mcp("getParameters", {"elementId": elem_id})

        family_name = ""
        type_name = ""
        mark = ""
        level = ""

        if params_r.get("success"):
            params = params_r.get("parameters", [])
            for p in params:
                name = p.get("name", "")
                value = p.get("value", "")
                if name == "Family":
                    family_name = value
                elif name == "Type":
                    type_name = value
                elif name == "Mark":
                    mark = value
                elif name == "Level":
                    level = value

        # For doors, get more specific info
        if category == "Doors":
            info = call_mcp("getDoorWindowInfo", {"elementId": elem_id})
            if info.get("success"):
                family_name = info.get("familyName", "")
                type_name = info.get("typeName", "")
                loc = info.get("location", [0, 0, 0])
                print(f"  ID {elem_id}: {family_name} - {type_name}")
                print(f"    Mark: {mark}, Location: ({loc[0]:.1f}, {loc[1]:.1f})")
            continue

        # Display element info
        display_type = type_name if type_name else family_name
        if display_type:
            if mark:
                print(f"  ID {elem_id}: {display_type} (Mark: {mark})")
            else:
                print(f"  ID {elem_id}: {display_type}")
        else:
            print(f"  ID {elem_id}")

    if len(elements) > 20:
        print(f"  ... and {len(elements) - 20} more")

# Summary
print("\n\n" + "=" * 70)
print("SUMMARY - ELEMENTS TO TRANSFER")
print("=" * 70)
for category, elements in results.items():
    print(f"  {category}: {len(elements)} elements")

# Find door D10 specifically
print("\n\n" + "=" * 70)
print("LOOKING FOR DOOR D10 (SLIDING DOOR)")
print("=" * 70)

doors = results.get("Doors", [])
d10_door = None

for door in doors:
    door_id = door.get("id")
    params_r = call_mcp("getParameters", {"elementId": door_id})
    if params_r.get("success"):
        params = params_r.get("parameters", [])
        for p in params:
            if p.get("name") == "Mark" and p.get("value") == "D10":
                info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
                if info.get("success"):
                    d10_door = {
                        "id": door_id,
                        "family": info.get("familyName"),
                        "type": info.get("typeName"),
                        "typeId": info.get("typeId"),
                        "location": info.get("location"),
                        "hostId": info.get("hostId")
                    }
                    print(f"Found Door D10:")
                    print(f"  Element ID: {door_id}")
                    print(f"  Family: {info.get('familyName')}")
                    print(f"  Type: {info.get('typeName')}")
                    print(f"  Type ID: {info.get('typeId')}")
                    loc = info.get('location', [0,0,0])
                    print(f"  Location: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})")
                break

if not d10_door:
    print("Door D10 not found by mark. Listing all sliding doors:")
    for door in doors:
        door_id = door.get("id")
        info = call_mcp("getDoorWindowInfo", {"elementId": door_id})
        if info.get("success"):
            family = info.get("familyName", "").lower()
            if "slid" in family:
                print(f"  ID {door_id}: {info.get('familyName')} - {info.get('typeName')}")

win32file.CloseHandle(pipe)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
