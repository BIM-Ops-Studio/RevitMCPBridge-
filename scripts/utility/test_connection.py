import win32file, json
try:
    h = win32file.CreateFile(r'\\.\pipe\RevitMCPBridge2026', win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
    win32file.WriteFile(h, b'{"method":"listKnownFirms","parameters":{}}')
    _, data = win32file.ReadFile(h, 64*1024)
    win32file.CloseHandle(h)
    result = json.loads(data)
    if result.get("success"):
        print(f"SUCCESS! Found {len(result.get('firms', []))} firms in database")
        for firm in result.get('firms', [])[:5]:
            print(f"  - {firm['firmName']} -> Pattern {firm['pattern']}")
    else:
        print(f"ERROR: {result.get('error')}")
except Exception as e:
    print(f"Connection error: {e}")
