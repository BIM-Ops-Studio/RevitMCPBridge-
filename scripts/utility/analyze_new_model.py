"""
Analyze what's in the new model - complete inventory
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
print("COMPLETE INVENTORY OF NEW MODEL", flush=True)
print("=" * 70, flush=True)

categories = ["Casework", "Plumbing Fixtures", "Furniture"]

all_types = {}

for category in categories:
    r = call_mcp("getFamilyInstanceTypes", {"category": category})
    if r.get("success"):
        types = r.get("familyTypes", [])
        all_types[category] = types

        print(f"\n{'='*70}", flush=True)
        print(f"{category.upper()}: {len(types)} types", flush=True)
        print("=" * 70, flush=True)

        # Group by family
        families = {}
        for t in types:
            fam = t.get("familyName", "Unknown")
            if fam not in families:
                families[fam] = []
            families[fam].append(t)

        for fam_name, fam_types in sorted(families.items()):
            print(f"\n  Family: {fam_name}", flush=True)
            for t in fam_types:
                print(f"    - {t.get('typeName')} (ID: {t.get('typeId')})", flush=True)

# Save for reference
with open("D:\\RevitMCPBridge2026\\new_model_types.json", 'w') as f:
    json.dump(all_types, f, indent=2)

win32file.CloseHandle(pipe)

print(f"\n\nSaved to: new_model_types.json", flush=True)
