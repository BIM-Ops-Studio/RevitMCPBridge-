import win32file
import json
import time

for attempt in range(3):
    try:
        print(f"Attempt {attempt + 1}...")
        h = win32file.CreateFile(
            r'\\.\pipe\RevitMCPBridge2026',
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        request = json.dumps({"method": "getLevels", "parameters": {}}).encode()
        win32file.WriteFile(h, request)

        _, data = win32file.ReadFile(h, 64*1024)
        win32file.CloseHandle(h)

        result = json.loads(data.decode())
        if result.get("success"):
            print(f"✓ MCP Bridge is ACTIVE!")
            print(f"✓ Found {len(result.get('levels', []))} levels in model")
            for level in result.get('levels', [])[:3]:
                print(f"  - {level.get('name')} @ {level.get('elevation')}'")
            break
        else:
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Connection error: {e}")
        if attempt < 2:
            print("  Waiting 2 seconds...")
            time.sleep(2)
