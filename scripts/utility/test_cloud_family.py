"""
Test the openLoadAutodeskFamilyDialog method
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
print("TESTING CLOUD FAMILY LOADING", flush=True)
print("=" * 70, flush=True)

print("\nCalling openLoadAutodeskFamilyDialog...", flush=True)
result = call_mcp("openLoadAutodeskFamilyDialog", {})

print(f"\nResult: {json.dumps(result, indent=2)}", flush=True)

if result.get("success"):
    print("\nThe 'Load Autodesk Family' dialog should now open in Revit!", flush=True)
else:
    print(f"\nError: {result.get('error')}", flush=True)

win32file.CloseHandle(pipe)
print("\nDone!", flush=True)
