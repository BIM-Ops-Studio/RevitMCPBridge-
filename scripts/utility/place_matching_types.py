"""
Place elements using matching family types from original model
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
print("PLACING ELEMENTS WITH MATCHING TYPES", flush=True)
print("=" * 70, flush=True)

# Load extracted data from original model
with open("D:\\RevitMCPBridge2026\\elements_with_types.json", 'r') as f:
    original_data = json.load(f)

# Get available types in new model
print("\n[1] GETTING AVAILABLE TYPES IN NEW MODEL", flush=True)

categories = {
    "Casework": "Casework",
    "Plumbing Fixtures": "Plumbing Fixtures",
    "Furniture": "Furniture"
}

new_model_types = {}
for display_name, category in categories.items():
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        new_model_types[category] = types
        print(f"  {display_name}: {len(types)} types", flush=True)
    else:
        new_model_types[category] = []

def find_matching_type(elem_name, available_types):
    """Find a matching type by name"""
    # Direct name match in fullName
    for t in available_types:
        full_name = t.get("fullName", "")
        type_name = t.get("typeName", "")
        family_name = t.get("familyName", "")

        # Exact match on type name
        if elem_name == type_name:
            return t

        # Check if element name is in full name
        if elem_name in full_name:
            return t

    # Partial match - element name contains key words
    elem_lower = elem_name.lower()
    for t in available_types:
        full_lower = t.get("fullName", "").lower()
        type_lower = t.get("typeName", "").lower()

        # Check for dimension matches
        if elem_lower in type_lower or elem_lower in full_lower:
            return t

        # Special cases
        if "toilet" in elem_lower and "toilet" in full_lower:
            return t
        if "tub" in elem_lower and "tub" in full_lower:
            return t
        if "queen" in elem_lower and "queen" in full_lower:
            return t
        if "king" in elem_lower and "king" in full_lower:
            return t
        if "credenza" in elem_lower and "credenza" in full_lower:
            return t
        if "filler" in elem_lower and "filler" in full_lower:
            return t

    return None

# Get level
print("\n[2] GETTING LEVEL", flush=True)
r = call_mcp("getLevels", {})
level_id = None
if r.get("success"):
    levels = r.get("levels", [])
    for level in levels:
        if "1" in level.get("name", "") or "First" in level.get("name", ""):
            level_id = level.get("levelId")
            print(f"  Using level: {level.get('name')} (ID: {level_id})", flush=True)
            break
    if not level_id and levels:
        level_id = levels[0].get("levelId")
        print(f"  Using first level: {levels[0].get('name')}", flush=True)

# Place elements
print("\n[3] PLACING ELEMENTS", flush=True)

results = {"success": 0, "failed": 0, "no_match": 0}
placement_log = []

for category in ["Casework", "Plumbing Fixtures", "Furniture"]:
    elements = original_data.get(category, [])
    available_types = new_model_types.get(category, [])

    if not available_types:
        print(f"\n{category}: SKIPPED - No types available", flush=True)
        results["failed"] += len(elements)
        continue

    print(f"\n{category}: Placing {len(elements)} elements", flush=True)

    for i, elem in enumerate(elements):
        elem_name = elem.get("name", "Unknown")
        loc = elem.get("location")
        rotation = elem.get("rotation", 0)

        if not loc:
            print(f"  [{i+1}] SKIPPED - No location for {elem_name}", flush=True)
            results["failed"] += 1
            continue

        # Find matching type
        matched_type = find_matching_type(elem_name, available_types)

        if not matched_type:
            # Use first available type as fallback
            matched_type = available_types[0]
            results["no_match"] += 1
            print(f"  [{i+1}] No match for '{elem_name}' - using {matched_type.get('fullName')}", flush=True)

        type_id = matched_type.get("typeId")
        type_name = matched_type.get("fullName")

        # Place the element
        params = {
            "familyTypeId": type_id,
            "location": loc,
            "rotation": rotation
        }
        if level_id:
            params["levelId"] = level_id

        r = call_mcp("placeFamilyInstance", params)

        if r.get("success"):
            results["success"] += 1
            placement_log.append({
                "original": elem_name,
                "placed": type_name,
                "location": loc
            })
            if (i + 1) % 5 == 0 or i == len(elements) - 1:
                print(f"  Placed {i+1}/{len(elements)}...", flush=True)
        else:
            results["failed"] += 1
            print(f"  [{i+1}] FAILED: {elem_name} - {r.get('error', 'Unknown')[:50]}", flush=True)

        time.sleep(0.05)

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70, flush=True)
print("PLACEMENT COMPLETE", flush=True)
print("=" * 70, flush=True)
print(f"  Success: {results['success']}", flush=True)
print(f"  Failed: {results['failed']}", flush=True)
print(f"  No exact match (used fallback): {results['no_match']}", flush=True)
print(f"  Total: {results['success'] + results['failed']}", flush=True)

# Show what was placed
print("\n" + "=" * 70, flush=True)
print("PLACEMENT LOG", flush=True)
print("=" * 70, flush=True)
for log in placement_log[:20]:
    print(f"  {log['original']} -> {log['placed']}", flush=True)
if len(placement_log) > 20:
    print(f"  ... and {len(placement_log) - 20} more", flush=True)
