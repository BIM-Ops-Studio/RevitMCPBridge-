"""
Test ping command to verify which DLL version is loaded
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

print("Testing ping to verify DLL version...")
print("=" * 60)

result = send_mcp_command("ping", {})

print("\nResult:")
print(json.dumps(result, indent=2))

if "testMessage" in result:
    print(f"\nTest Message: {result['testMessage']}")
    if "NEW_DLL_v1.0.3.0" in result["testMessage"]:
        print("[SUCCESS] New DLL v1.0.3.0 is loaded!")
    else:
        print(f"[WARNING] Old DLL is still loaded. Expected v1.0.3.0, got: {result.get('assemblyVersion', 'unknown')}")
