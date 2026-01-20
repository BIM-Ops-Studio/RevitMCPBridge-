"""
Place elements at exact locations with precise type matching
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
print("PRECISE ELEMENT PLACEMENT", flush=True)
print("=" * 70, flush=True)

# Load extracted data with exact locations
with open("D:\\RevitMCPBridge2026\\elements_with_types.json", 'r') as f:
    original_data = json.load(f)

# Get available types
print("\n[1] AVAILABLE TYPES IN NEW MODEL", flush=True)

categories = ["Casework", "Plumbing Fixtures", "Furniture"]
available_types = {}

for category in categories:
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        available_types[category] = types
        print(f"\n{category}: {len(types)} types", flush=True)
        for t in types:
            print(f"  - {t.get('fullName')}", flush=True)

# Build type mappings based on what's available
print("\n\n[2] BUILDING TYPE MAPPINGS", flush=True)

type_map = {}

# Furniture mappings
for t in available_types.get("Furniture", []):
    name = t.get("fullName", "").lower()
    if "queen" in name:
        type_map["QUEEN 60\" x 80\""] = t
        print(f"  QUEEN bed -> {t.get('fullName')}", flush=True)
    if "king" in name:
        type_map["KING 76\" x 80\""] = t
        print(f"  KING bed -> {t.get('fullName')}", flush=True)
    if "nightstand" in name or "night stand" in name or "night-stand" in name:
        type_map["18\" x 22\" x 24\""] = t
        print(f"  Nightstand -> {t.get('fullName')}", flush=True)
    if "credenza" in name:
        type_map["CREDENZA-56x18"] = t
        print(f"  Credenza -> {t.get('fullName')}", flush=True)

# Plumbing mappings
for t in available_types.get("Plumbing Fixtures", []):
    name = t.get("fullName", "").lower()
    if "toilet" in name:
        type_map["Toilet-Domestic-3D"] = t
        print(f"  Toilet -> {t.get('fullName')}", flush=True)
    if "tub" in name:
        type_map["Tub-Rectangular-3D"] = t
        print(f"  Tub -> {t.get('fullName')}", flush=True)
    if "lavatory" in name or "lav" in name:
        # Map sink sizes
        if "20" in name and "18" in name:
            type_map["20\" x 18\""] = t
            print(f"  Lavatory 20x18 -> {t.get('fullName')}", flush=True)
    if "sink" in name:
        if "42" in name:
            type_map["42\" x 21\""] = t
            print(f"  Sink 42x21 -> {t.get('fullName')}", flush=True)
        if "54" in name or "30" in name:
            type_map["54\" x 30\""] = t
            print(f"  Sink 54x30 -> {t.get('fullName')}", flush=True)

# Casework mappings
for t in available_types.get("Casework", []):
    name = t.get("fullName", "").lower()
    type_name = t.get("typeName", "")

    # Match by exact dimension
    if "24\" depth" in name.lower() or type_name == "24\" Depth":
        type_map["24\" Depth"] = t
    if "48\"" in type_name and "depth" not in type_name.lower():
        type_map["48\""] = t
    if "36\"" in type_name and "depth" not in type_name.lower():
        type_map["36\""] = t
    if "24\"" in type_name and "depth" not in type_name.lower() and "aff" not in type_name.lower():
        type_map["24\""] = t
    if "18\"" in type_name and "depth" not in type_name.lower() and "aff" not in type_name.lower():
        type_map["18\""] = t
    if "filler" in name:
        type_map["Base Cabinet-Filler"] = t
        print(f"  Cabinet Filler -> {t.get('fullName')}", flush=True)
    if "countertop" in name or "counter" in name:
        if "18" in name and "34" in name:
            type_map["18\" @ 34 AFF"] = t
        if "24" in name and "36" in name:
            type_map["24\" @ 36 AFF"] = t

# Get level
print("\n[3] GETTING LEVEL", flush=True)
r = call_mcp("getLevels", {})
level_id = None
if r.get("success"):
    levels = r.get("levels", [])
    for level in levels:
        level_id = level.get("levelId")
        print(f"  Using: {level.get('name')} (ID: {level_id})", flush=True)
        break

# Place elements
print("\n[4] PLACING ELEMENTS AT EXACT LOCATIONS", flush=True)

results = {"success": 0, "failed": 0, "no_type": 0}

for category in categories:
    elements = original_data.get(category, [])
    fallback_types = available_types.get(category, [])

    if not fallback_types:
        print(f"\n{category}: SKIPPED - No types", flush=True)
        continue

    print(f"\n{category}: {len(elements)} elements", flush=True)

    for i, elem in enumerate(elements):
        elem_name = elem.get("name", "Unknown")
        loc = elem.get("location")
        rotation = elem.get("rotation", 0)

        if not loc:
            results["failed"] += 1
            continue

        # Find type
        matched_type = type_map.get(elem_name)

        if not matched_type:
            # Try partial match
            for key, val in type_map.items():
                if key.lower() in elem_name.lower() or elem_name.lower() in key.lower():
                    matched_type = val
                    break

        if not matched_type:
            # Use first available as fallback
            matched_type = fallback_types[0]
            results["no_type"] += 1
            print(f"  [{i+1}] No type for '{elem_name}' - using {matched_type.get('fullName')}", flush=True)

        # Place at exact location
        params = {
            "familyTypeId": matched_type.get("typeId"),
            "location": loc,
            "rotation": rotation
        }
        if level_id:
            params["levelId"] = level_id

        r = call_mcp("placeFamilyInstance", params)

        if r.get("success"):
            results["success"] += 1
            print(f"  [{i+1}] {elem_name} at ({loc[0]:.1f}, {loc[1]:.1f}) rot={rotation:.0f}°", flush=True)
        else:
            results["failed"] += 1
            print(f"  [{i+1}] FAILED: {elem_name} - {r.get('error', '')[:40]}", flush=True)

        time.sleep(0.1)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70, flush=True)
print("PLACEMENT COMPLETE", flush=True)
print("=" * 70, flush=True)
print(f"  Success: {results['success']}", flush=True)
print(f"  No matching type (used fallback): {results['no_type']}", flush=True)
print(f"  Failed: {results['failed']}", flush=True)
