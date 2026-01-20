"""
Test wall creation with verbose error output
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

# Get level ID
print("Getting level ID...")
levels_result = send_mcp_command("getLevels", {})
level_id = levels_result["levels"][0]["levelId"]
print(f"Using level ID: {level_id}")

# Try creating a single wall
print("\nAttempting to create walls...")
walls_data = {
    "walls": [
        {
            "startPoint": [0, 0, 0],
            "endPoint": [45.333, 0, 0],
            "levelId": level_id,
            "height": 10.0
        }
    ]
}

print("\nSending request:")
print(json.dumps(walls_data, indent=2))

result = send_mcp_command("batchCreateWalls", walls_data)

print("\nFull response:")
print(json.dumps(result, indent=2))
