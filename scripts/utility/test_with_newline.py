import win32file, json

try:
    print("Connecting to MCP server...")
    h = win32file.CreateFile(
        r'\\.\pipe\RevitMCPBridge2026',
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )

    # Send message WITH newline at end (required by ReadLineAsync)
    message = b'{"method":"getAllSheets","parameters":{}}\n'
    print(f"Sending: {message}")
    win32file.WriteFile(h, message)

    print("Waiting for response...")
    # Read until we get a complete JSON response (ends with newline)
    chunks = []
    while True:
        _, data = win32file.ReadFile(h, 8192)
        chunks.append(data)
        if b'\n' in data or len(data) == 0:
            break
    win32file.CloseHandle(h)

    response = b''.join(chunks).decode().strip()
    print(f"Response length: {len(response)} chars")

    try:
        result = json.loads(response)
        if result.get("success"):
            print("SUCCESS!")
            data = result.get('result', result)
            sheets = data.get('sheets', [])
            total = data.get('totalSheets', len(sheets))
            print(f"Found {total} sheets")
            for sheet in sheets[:5]:
                print(f"  - {sheet.get('sheetNumber', 'N/A')}: {sheet.get('sheetName', 'N/A')}")
        else:
            print(f"ERROR: {result.get('error')}")
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        print(f"First 500 chars: {response[:500]}")

except Exception as e:
    print(f"Connection error: {e}")
