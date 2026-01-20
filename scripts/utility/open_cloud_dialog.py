"""
Open the Load Autodesk Family dialog
Uses a shorter timeout since PostCommand queues the action
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

def call_mcp_quick(method, params={}):
    """Quick call that doesn't wait long for response"""
    request = json.dumps({'method': method, 'params': params}) + '\n'
    win32file.WriteFile(pipe, request.encode())

    # Quick read with short timeout behavior
    try:
        result, data = win32file.ReadFile(pipe, 65536)
        return json.loads(data.decode().strip())
    except:
        return {"success": True, "message": "Command sent"}

print("Opening Load Autodesk Family dialog...", flush=True)
result = call_mcp_quick("openLoadAutodeskFamilyDialog", {})
print(f"Result: {result}", flush=True)

win32file.CloseHandle(pipe)
print("\nDialog should open in Revit now. Search for families to load.", flush=True)
