import win32file, json, time

def call_mcp_single(method, params={}, retries=5):
    """Single call per connection with retry logic"""
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
                time.sleep(0.3)  # Wait before retry
            continue
    return {"success": False, "error": last_error}

# Step 1: Find the text elements
print("Step 1: Searching for 'CYCLE GEAR' text...")
result = call_mcp_single("findTextNotesByContent", {"searchPattern": "CYCLE GEAR"})

if not result.get("success"):
    print(f"ERROR: {result.get('error')}")
    exit(1)

matches = result.get("result", {}).get("matches", [])
print(f"Found {len(matches)} text elements")

if not matches:
    print("No text elements found!")
    exit(1)

# Get the text element info
text_id = matches[0]["id"]
view_id = matches[0]["viewId"]
print(f"  Element ID: {text_id}")
print(f"  View ID: {view_id}")

# Wait for server to reset connection
time.sleep(0.5)

# Step 2: Override first element to RED
print(f"\nStep 2: Changing text element {text_id} to RED...")
override_result = call_mcp_single("overrideElementGraphics", {
    "viewId": view_id,
    "elementId": text_id,
    "lineColor": {"r": 255, "g": 0, "b": 0}
})

if override_result.get("success"):
    print("SUCCESS! First text element is now RED.")
    print(json.dumps(override_result, indent=2))
else:
    print(f"ERROR: {override_result.get('error')}")

# Step 3: Override second element if exists
if len(matches) > 1:
    # Wait for server to reset connection
    time.sleep(0.5)

    text_id_2 = matches[1]["id"]
    print(f"\nStep 3: Changing second text element {text_id_2} to RED...")
    override_result_2 = call_mcp_single("overrideElementGraphics", {
        "viewId": view_id,
        "elementId": text_id_2,
        "lineColor": {"r": 255, "g": 0, "b": 0}
    })

    if override_result_2.get("success"):
        print("SUCCESS! Second text element is now RED.")
        print(json.dumps(override_result_2, indent=2))
    else:
        print(f"ERROR: {override_result_2.get('error')}")

print("\nDone! Check your Revit view - the text should be RED now.")
