"""
Test creating a level to verify document modification works
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

print("Testing document modification by creating a level...")
print("=" * 60)

# Try to create a new level at elevation 20'
level_params = {
    "name": "Test Level",
    "elevation": 20.0
}

print(f"\nAttempting to create level: {level_params['name']} @ {level_params['elevation']}'")
result = send_mcp_command("createLevel", level_params)

print("\nResult:")
print(json.dumps(result, indent=2))

if result.get("success"):
    print("\n[SUCCESS] Level creation works! Document modification is functional.")
else:
    print(f"\n[FAILED] {result.get('error')}")
