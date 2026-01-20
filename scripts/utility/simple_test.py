import win32file
import json

try:
    print("Connecting to MCP bridge...")
    h = win32file.CreateFile(
        r'\\.\pipe\RevitMCPBridge2026',
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None
    )
    print("Connected! Sending getLevels command...")

    request = (json.dumps({"method": "getLevels", "parameters": {}}) + "\n").encode()
    win32file.WriteFile(h, request)
    print("Command sent, waiting for response...")

    _, data = win32file.ReadFile(h, 64*1024)
    print("Response received!")
    win32file.CloseHandle(h)

    result = json.loads(data.decode())
    if result.get("success"):
        print(f"SUCCESS! Found {len(result.get('levels', []))} levels")
        for level in result.get('levels', [])[:5]:
            print(f"  - {level.get('name')} @ {level.get('elevation')}'")
    else:
        print(f"ERROR: {result.get('error')}")
except Exception as e:
    print(f"Connection error: {e}")
