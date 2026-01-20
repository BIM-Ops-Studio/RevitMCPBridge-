"""
Delete all existing elements and place with correct types
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
print("DELETE ALL AND REPLACE WITH CORRECT TYPES", flush=True)
print("=" * 70, flush=True)

categories = ["Casework", "Plumbing Fixtures", "Furniture"]

# Step 1: Delete all existing elements
print("\n[1] DELETING EXISTING ELEMENTS", flush=True)
total_deleted = 0

for category in categories:
    r = call_mcp("getElements", {"category": category})
    elements = r.get("result", {}).get("elements", [])

    if elements:
        print(f"  {category}: Deleting {len(elements)} elements...", flush=True)

        element_ids = [elem.get("id") for elem in elements]

        # Delete in batches
        for i in range(0, len(element_ids), 10):
            batch = element_ids[i:i+10]
            for elem_id in batch:
                r = call_mcp("deleteElement", {"elementId": elem_id})
                if r.get("success"):
                    total_deleted += 1
            time.sleep(0.05)

        print(f"    Deleted {len(elements)} elements", flush=True)
    else:
        print(f"  {category}: No elements to delete", flush=True)

print(f"\n  Total deleted: {total_deleted}", flush=True)

# Step 2: Get available types in the updated model
print("\n[2] GETTING AVAILABLE TYPES (UPDATED)", flush=True)

new_model_types = {}
for category in categories:
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        new_model_types[category] = types
        print(f"  {category}: {len(types)} types", flush=True)

        # Show types for debugging
        for t in types[:10]:
            print(f"    - {t.get('fullName')}", flush=True)
        if len(types) > 10:
            print(f"    ... and {len(types) - 10} more", flush=True)
    else:
        new_model_types[category] = []

# Load original data
with open("D:\\RevitMCPBridge2026\\elements_with_types.json", 'r') as f:
    original_data = json.load(f)

# Step 3: Get level
print("\n[3] GETTING LEVEL", flush=True)
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

# Step 4: Place elements with better matching
print("\n[4] PLACING ELEMENTS WITH MATCHING TYPES", flush=True)

def find_best_match(elem_name, available_types):
    """Find best matching type"""
    elem_lower = elem_name.lower().strip()

    # Build search terms from element name
    # Remove common suffixes
    search_term = elem_lower

    best_match = None
    best_score = 0

    for t in available_types:
        full_name = t.get("fullName", "").lower()
        type_name = t.get("typeName", "").lower()
        family_name = t.get("familyName", "").lower()

        score = 0

        # Exact type name match
        if elem_lower == type_name:
            return t  # Perfect match

        # Check if element name contains key identifiers
        if "toilet" in elem_lower and "toilet" in full_name:
            score += 100
        if "tub" in elem_lower and "tub" in full_name:
            score += 100
        if "queen" in elem_lower and "queen" in full_name:
            score += 100
        if "king" in elem_lower and "king" in full_name:
            score += 100
        if "credenza" in elem_lower and "credenza" in full_name:
            score += 100
        if "nightstand" in elem_lower or ("18" in elem_lower and "22" in elem_lower and "24" in elem_lower):
            if "nightstand" in full_name or "night" in full_name:
                score += 100
        if "filler" in elem_lower and "filler" in full_name:
            score += 100
        if "lavatory" in full_name or "sink" in full_name:
            if "x" in elem_lower:  # Dimension format like "20" x 18""
                score += 50

        # Dimension matching
        # Extract dimensions from element name
        import re
        elem_dims = re.findall(r'(\d+)"', elem_lower)
        type_dims = re.findall(r'(\d+)"', full_name)

        if elem_dims and type_dims:
            for dim in elem_dims:
                if dim in type_dims:
                    score += 20

        # Partial name match
        if elem_lower in full_name or elem_lower in type_name:
            score += 30

        if score > best_score:
            best_score = score
            best_match = t

    return best_match

results = {"success": 0, "failed": 0, "matched": 0, "fallback": 0}

for category in categories:
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
            results["failed"] += 1
            continue

        # Find matching type
        matched_type = find_best_match(elem_name, available_types)

        if matched_type:
            results["matched"] += 1
        else:
            matched_type = available_types[0]
            results["fallback"] += 1
            print(f"  [{i+1}] No match: '{elem_name}' -> {matched_type.get('fullName')}", flush=True)

        type_id = matched_type.get("typeId")

        # Place element
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
            if (i + 1) % 10 == 0 or i == len(elements) - 1:
                print(f"  Placed {i+1}/{len(elements)}...", flush=True)
        else:
            results["failed"] += 1
            print(f"  [{i+1}] FAILED: {r.get('error', 'Unknown')[:50]}", flush=True)

        time.sleep(0.05)

win32file.CloseHandle(pipe)

# Summary
print("\n" + "=" * 70, flush=True)
print("COMPLETE", flush=True)
print("=" * 70, flush=True)
print(f"  Deleted: {total_deleted}", flush=True)
print(f"  Placed: {results['success']}", flush=True)
print(f"  Matched types: {results['matched']}", flush=True)
print(f"  Used fallback: {results['fallback']}", flush=True)
print(f"  Failed: {results['failed']}", flush=True)
