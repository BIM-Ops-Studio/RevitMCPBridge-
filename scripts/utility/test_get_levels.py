"""
Test getLevels response structure
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

# Get levels and print full response
print("Calling getLevels...")
result = send_mcp_command("getLevels", {})

print("\nFull response:")
print(json.dumps(result, indent=2))

if result.get("success"):
    levels = result.get("levels", [])
    print(f"\nFound {len(levels)} levels:")
    for i, level in enumerate(levels):
        print(f"\nLevel {i}:")
        print(f"  Keys: {list(level.keys())}")
        for key, value in level.items():
            print(f"  {key}: {value}")
