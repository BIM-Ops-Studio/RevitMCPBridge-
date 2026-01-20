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
    print("Connected!")

    request = (json.dumps({"method": "ping", "parameters": {}}) + "\n").encode()
    win32file.WriteFile(h, request)
    print("Ping sent...")

    _, data = win32file.ReadFile(h, 64*1024)
    print("Response received!")
    win32file.CloseHandle(h)

    result = json.loads(data.decode())
    print(f"Result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
