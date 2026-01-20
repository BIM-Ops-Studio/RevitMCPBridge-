"""
Check available door types and find the one we're trying to use
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

print("=" * 60)
print("CHECKING DOOR TYPES")
print("=" * 60)

r = call_mcp("getDoorTypes", {})
if r.get("success"):
    door_types = r.get("doorTypes", [])
    print(f"\nFound {len(door_types)} door types\n")

    # Check if our test type exists
    target_id = 387958
    found = False

    print("Looking for Door-Passage-Single-Flush types:")
    for dt in door_types:
        type_id = dt.get('typeId')
        family = dt.get('familyName', '')
        name = dt.get('typeName', '')

        if 'Passage' in family or 'Flush' in family:
            marker = " <-- TEST TYPE" if type_id == target_id else ""
            print(f"  {family} - {name}")
            print(f"    TypeID: {type_id}{marker}")
            if type_id == target_id:
                found = True

    if not found:
        print(f"\n*** Target type ID {target_id} NOT FOUND ***")
        print("\nFirst 5 available door types:")
        for dt in door_types[:5]:
            print(f"  {dt.get('familyName')} - {dt.get('typeName')}: {dt.get('typeId')}")
else:
    print(f"Error: {r.get('error')}")

win32file.CloseHandle(pipe)
