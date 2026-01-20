"""
Place all casework, plumbing fixtures, and furniture in the new model
Uses extracted locations and rotations from the original model
"""
import win32file
import json
import sys
import time

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
print("PLACING ALL ELEMENTS IN NEW MODEL", flush=True)
print("=" * 70, flush=True)

# Load extracted data
with open("D:\\RevitMCPBridge2026\\element_locations.json", 'r') as f:
    data = json.load(f)

# Get available types in new model
print("\n[1] GETTING AVAILABLE TYPES IN NEW MODEL", flush=True)

categories = {
    "Casework": "Casework",
    "Plumbing Fixtures": "Plumbing Fixtures",
    "Furniture": "Furniture"
}

available_types = {}
for display_name, category in categories.items():
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        available_types[category] = types
        print(f"  {display_name}: {len(types)} types available", flush=True)
        if types:
            # Show first type as default
            print(f"    Default: {types[0].get('fullName')}", flush=True)
    else:
        print(f"  {display_name}: ERROR - {r.get('error')}", flush=True)
        available_types[category] = []

# Get level ID (assuming First Floor)
print("\n[2] GETTING LEVEL", flush=True)
r = call_mcp("getLevels", {})
level_id = None
if r.get("success"):
    levels = r.get("levels", [])
    for level in levels:
        if "First" in level.get("name", "") or level.get("elevation", 0) == 0:
            level_id = level.get("levelId")
            print(f"  Using level: {level.get('name')} (ID: {level_id})", flush=True)
            break
    if not level_id and levels:
        level_id = levels[0].get("levelId")
        print(f"  Using first level: {levels[0].get('name')} (ID: {level_id})", flush=True)

# Place elements
print("\n[3] PLACING ELEMENTS", flush=True)

results = {"success": 0, "failed": 0}

for category in ["Casework", "Plumbing Fixtures", "Furniture"]:
    elements = data.get(category, [])
    types = available_types.get(category, [])

    if not types:
        print(f"\n{category}: SKIPPED - No types available", flush=True)
        results["failed"] += len(elements)
        continue

    # Use first type as default
    default_type_id = types[0].get("typeId")
    default_type_name = types[0].get("fullName")

    print(f"\n{category}: Placing {len(elements)} elements", flush=True)
    print(f"  Using type: {default_type_name}", flush=True)

    for i, elem in enumerate(elements):
        loc = elem.get("location")
        rotation = elem.get("rotation", 0)

        if not loc:
            print(f"  [{i+1}] SKIPPED - No location", flush=True)
            results["failed"] += 1
            continue

        # Place the element
        params = {
            "familyTypeId": default_type_id,
            "location": loc,
            "rotation": rotation
        }
        if level_id:
            params["levelId"] = level_id

        r = call_mcp("placeFamilyInstance", params)

        if r.get("success"):
            results["success"] += 1
            if (i + 1) % 5 == 0 or i == len(elements) - 1:
                print(f"  Placed {i+1}/{len(elements)}...", flush=True)
        else:
            results["failed"] += 1
            print(f"  [{i+1}] FAILED: {r.get('error', 'Unknown')[:50]}", flush=True)

        time.sleep(0.05)  # Small delay between placements

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70, flush=True)
print("PLACEMENT COMPLETE", flush=True)
print("=" * 70, flush=True)
print(f"  Success: {results['success']}", flush=True)
print(f"  Failed: {results['failed']}", flush=True)
print(f"  Total: {results['success'] + results['failed']}", flush=True)

if results["success"] == 57:
    print("\nAll 57 elements placed successfully!", flush=True)
elif results["success"] > 0:
    print(f"\n{results['success']} elements placed. Check Revit for results.", flush=True)
