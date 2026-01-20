import win32file, json, time

def call_mcp(method, params={}, retries=5):
    """Call MCP with retry logic"""
    last_error = None
    for attempt in range(retries):
        try:
            h = win32file.CreateFile(
                r'\\.\pipe\RevitMCPBridge2026',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None, win32file.OPEN_EXISTING, 0, None
            )
            message = json.dumps({"method": method, "params": params}).encode() + b'\n'
            win32file.WriteFile(h, message)

            chunks = []
            while True:
                _, data = win32file.ReadFile(h, 8192)
                chunks.append(data)
                if b'\n' in data or len(data) == 0:
                    break
            win32file.CloseHandle(h)

            return json.loads(b''.join(chunks).decode().strip())
        except Exception as e:
            last_error = str(e)
            if attempt < retries - 1:
                time.sleep(0.3)
            continue
    return {"success": False, "error": last_error}

# The new text element IDs
RED_TEXT_ID = 2553438
BLACK_TEXT_ID = 2553439

# 1/8 inch = 0.125 inches
TEXT_SIZE_INCHES = 0.125

print("=" * 60)
print("FIXING TEXT SIZE TO 1/8 INCH")
print("=" * 60)

# Fix the RED text element
print(f"\nChanging RED text (ID {RED_TEXT_ID}) to 1/8\" size...")
result1 = call_mcp("changeTextNoteType", {
    "elementId": RED_TEXT_ID,
    "textSizeInches": TEXT_SIZE_INCHES
})

if result1.get("success"):
    print("  SUCCESS! Red text is now 1/8\"")
else:
    print(f"  ERROR: {result1.get('error')}")

# Fix the BLACK text element
print(f"\nChanging BLACK text (ID {BLACK_TEXT_ID}) to 1/8\" size...")
result2 = call_mcp("changeTextNoteType", {
    "elementId": BLACK_TEXT_ID,
    "textSizeInches": TEXT_SIZE_INCHES
})

if result2.get("success"):
    print("  SUCCESS! Black text is now 1/8\"")
else:
    print(f"  ERROR: {result2.get('error')}")

print("\n" + "=" * 60)
print("DONE! Both texts should now be 1/8\" size.")
print("=" * 60)
