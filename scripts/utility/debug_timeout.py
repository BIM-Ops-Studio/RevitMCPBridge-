"""
Debug MCP Bridge Timeout Issue
Tests which operations work vs timeout
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
print("MCP BRIDGE TIMEOUT DEBUGGING")
print("=" * 60)

# Test 1: ping (no Revit context)
print("\n[1] Testing ping (no Revit context)...")
r = call_mcp("ping", {})
print(f"Result: {json.dumps(r, indent=2)}")
print(f"Success: {r.get('success', False)}")

# Test 2: getElements (uses Task.Run, not ExecuteInRevitContext)
print("\n[2] Testing getElements (Task.Run - should work)...")
r = call_mcp("getElements", {"category": "Walls"})
print(f"Success: {r.get('success', r.get('result', {}).get('success', 'N/A'))}")
elements = r.get("result", {}).get("elements", [])
print(f"Elements found: {len(elements)}")

# Test 3: getLevels (uses ExecuteInRevitContext)
print("\n[3] Testing getLevels (ExecuteInRevitContext)...")
r = call_mcp("getLevels", {})
print(f"Full response: {json.dumps(r, indent=2)}")
print(f"Success: {r.get('success', False)}")
if r.get('error'):
    print(f"ERROR: {r.get('error')}")

# Test 4: getDoorTypes (uses ExecuteInRevitContext)
print("\n[4] Testing getDoorTypes (ExecuteInRevitContext)...")
r = call_mcp("getDoorTypes", {})
print(f"Success: {r.get('success', False)}")
if r.get('error'):
    print(f"ERROR: {r.get('error')}")
else:
    print(f"Door types: {len(r.get('doorTypes', []))}")

# Test 5: getWallInfo (uses ExecuteInRevitContext)
print("\n[5] Testing getWallInfo (ExecuteInRevitContext)...")
if elements:
    first_wall = elements[0]["id"]
    r = call_mcp("getWallInfo", {"wallId": first_wall})
    print(f"Success: {r.get('success', False)}")
    if r.get('error'):
        print(f"ERROR: {r.get('error')}")
    else:
        print(f"Wall length: {r.get('length', 'N/A')}")
else:
    print("No walls to test with")

# Test 6: placeDoor (uses ExecuteInRevitContext with Transaction)
print("\n[6] Testing placeDoor (ExecuteInRevitContext with Transaction)...")
if elements:
    first_wall = elements[0]["id"]
    r = call_mcp("placeDoor", {
        "wallId": first_wall,
        "doorTypeId": 387958
    })
    print(f"Full response: {json.dumps(r, indent=2)}")
    print(f"Success: {r.get('success', False)}")
    if r.get('error'):
        print(f"ERROR: {r.get('error')}")
else:
    print("No walls to test with")

win32file.CloseHandle(pipe)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
If ping works but getLevels/getDoorTypes/getWallInfo timeout:
  -> External event not being processed by Revit

If getLevels/getDoorTypes work but placeDoor times out:
  -> Transaction is blocking or failing silently

Check Revit:
  - Is Revit idle? (no dialogs, not in command mode)
  - Is Revit minimized? (may affect idle loop)
  - Try clicking in Revit window to make it active
""")
