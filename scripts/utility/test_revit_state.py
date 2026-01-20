"""
Test Revit state - check if document is open
"""

import win32file
import json

def send_mcp_command(method, parameters):
    """Send command to Revit MCP Bridge"""
    try:
        h = win32file.CreateFile(
            r'\\.\pipe\RevitMCPBridge2026',
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        request = (json.dumps({"method": method, "parameters": parameters}) + "\n").encode()
        win32file.WriteFile(h, request)

        _, data = win32file.ReadFile(h, 64*1024)
        win32file.CloseHandle(h)

        result = json.loads(data.decode())
        return result
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

# Test various methods that don't modify the model
print("1. Testing getLevels...")
result = send_mcp_command("getLevels", {})
print(f"   Success: {result.get('success')}")
if result.get('success'):
    print(f"   Level count: {result.get('levelCount')}")
else:
    print(f"   Error: {result.get('error')}")

print("\n2. Testing getWallTypes...")
result = send_mcp_command("getWallTypes", {})
print(f"   Success: {result.get('success')}")
if result.get('success'):
    types = result.get('wallTypes', [])
    print(f"   Wall type count: {len(types)}")
    if types:
        print(f"   First type: {types[0].get('name')}")
else:
    print(f"   Error: {result.get('error')}")

print("\n3. Testing getViews...")
result = send_mcp_command("getViews", {})
print(f"   Success: {result.get('success')}")
if result.get('success'):
    views = result.get('views', [])
    print(f"   View count: {len(views)}")
else:
    print(f"   Error: {result.get('error')}")
