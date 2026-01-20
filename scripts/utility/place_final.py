"""
Final placement with explicit type ID mappings
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
print("FINAL PLACEMENT WITH CORRECT TYPES", flush=True)
print("=" * 70, flush=True)

# Load extracted data
with open("D:\\RevitMCPBridge2026\\elements_with_types.json", 'r') as f:
    original_data = json.load(f)

# Explicit type mappings based on new model inventory
# Format: original_name -> (typeId, description)
TYPE_MAP = {
    # FURNITURE
    "QUEEN 60\" x 80\"": (1258143, "FN-BED-RESIDENTIAL - QUEEN"),
    "KING 76\" x 80\"": (1258145, "FN-BED-RESIDENTIAL - KING"),
    "18\" x 22\" x 24\"": (1258710, "Table-Night Stand"),
    "CREDENZA-56x18": (1259562, "FN-MULTI - CREDENZA"),

    # PLUMBING
    "Tub-Rectangular-3D": (1255665, "Tub-Rectangular-3D"),
    "Toilet-Domestic-3D": (983995, "Water Closet - Flush Tank - Private"),
    "20\" x 18\"": (1256397, "Sink Vanity-Square 20x18"),
    "42\" x 21\"": (981995, "Sink Kitchen 42x21"),
    "54\" x 30\"": (981995, "Sink Kitchen (using 42x21 as closest)"),

    # CASEWORK
    "Base Cabinet-Filler": (1260069, "Base Cabinet-Filler"),
    "24\" Depth": (452399, "Counter Top 24\" Depth"),
    "48\"": (450599, "Base Cabinet 48\""),
    "36\"": (450591, "Base Cabinet 36\""),
    "24\"": (450585, "Base Cabinet 24\""),
    "33\"": (450589, "Base Cabinet 33\""),
    "45\"": (450597, "Base Cabinet 45\""),
    "18\"": (450585, "Base Cabinet 24\" (closest)"),
    "18\"D": (450585, "Base Cabinet 24\" (closest)"),
    "14\"": (450585, "Base Cabinet 24\" (closest)"),
    "15\"": (450585, "Base Cabinet 24\" (closest)"),
    "12\" Depth": (452399, "Counter Top 24\" Depth"),
    "24\" @ 36 AFF": (452399, "Counter Top 24\" Depth"),
    "18\" @ 34 AFF": (452399, "Counter Top 24\" Depth"),
    "36\" 2": (450591, "Base Cabinet 36\""),
    "31 7/8\"": (450583, "Base Cabinet 30\""),
    "29.5\"": (450583, "Base Cabinet 30\""),
}

# Get level
print("\n[1] GETTING LEVEL", flush=True)
r = call_mcp("getLevels", {})
level_id = None
if r.get("success"):
    levels = r.get("levels", [])
    if levels:
        level_id = levels[0].get("levelId")
        print(f"  Using: {levels[0].get('name')} (ID: {level_id})", flush=True)

# Place elements
print("\n[2] PLACING ELEMENTS", flush=True)

results = {"success": 0, "failed": 0, "no_map": 0}

for category in ["Casework", "Plumbing Fixtures", "Furniture"]:
    elements = original_data.get(category, [])

    print(f"\n{category}: {len(elements)} elements", flush=True)

    for i, elem in enumerate(elements):
        elem_name = elem.get("name", "Unknown")
        loc = elem.get("location")
        rotation = elem.get("rotation", 0)

        if not loc:
            results["failed"] += 1
            continue

        # Get type from map
        mapping = TYPE_MAP.get(elem_name)

        if not mapping:
            results["no_map"] += 1
            print(f"  [{i+1}] NO MAPPING: '{elem_name}'", flush=True)
            continue

        type_id, type_desc = mapping

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
            print(f"  [{i+1}] {elem_name} -> {type_desc}", flush=True)
            print(f"       at ({loc[0]:.1f}, {loc[1]:.1f}) rot={rotation:.0f}", flush=True)
        else:
            results["failed"] += 1
            print(f"  [{i+1}] FAILED: {elem_name} - {r.get('error', '')[:50]}", flush=True)

        time.sleep(0.1)

win32file.CloseHandle(pipe)

print("\n" + "=" * 70, flush=True)
print("PLACEMENT COMPLETE", flush=True)
print("=" * 70, flush=True)
print(f"  Success: {results['success']}", flush=True)
print(f"  No mapping: {results['no_map']}", flush=True)
print(f"  Failed: {results['failed']}", flush=True)
