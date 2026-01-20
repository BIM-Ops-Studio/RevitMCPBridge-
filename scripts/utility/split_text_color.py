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

# The text we're working with
ELEMENT_ID = 2553418
VIEW_ID = 2485963

# Text to make RED (first line only)
RED_TEXT = 'ADJACENT TENANT SPACE IS CYCLE GEAR – "M" OCCUPANCY (RETAIL MOTORCYCLE GEAR & ACCESSORIES)'

# Text to keep BLACK (remaining lines)
BLACK_TEXT = '''ADJACENT TENANT ADDRESS: 6371 W SAMPLE RD, CORAL SPRINGS, FL 33067
DEMISING WALL REQUIREMENT: 2-HR FIRE-RATED WALL ASSEMBLY (PER APPLICABLE FBC REQUIREMENTS & AHJ)'''

print("=" * 60)
print("SPLIT TEXT INTO RED AND BLACK")
print("=" * 60)

# Step 1: Get the original text element's position
print("\nStep 1: Getting original text element position...")
result = call_mcp("getTextElements", {"viewId": VIEW_ID, "searchText": "CYCLE GEAR"})

if not result.get("success"):
    print(f"ERROR: {result.get('error')}")
    exit(1)

# Find our element
elements = result.get("result", {}).get("textElements", [])
original = None
for elem in elements:
    if elem.get("id") == ELEMENT_ID:
        original = elem
        break

if not original:
    print(f"ERROR: Could not find element {ELEMENT_ID}")
    exit(1)

position = original.get("position", {})
orig_x = position.get("x", 0)
orig_y = position.get("y", 0)
orig_z = position.get("z", 0)
type_id = original.get("typeId", 0)

print(f"  Original position: ({orig_x:.4f}, {orig_y:.4f}, {orig_z:.4f})")
print(f"  Type ID: {type_id}")

# Step 2: First, let's clear the red override from the original
print("\nStep 2: Clearing red override from original...")
clear_result = call_mcp("clearElementGraphicsOverrides", {
    "viewId": VIEW_ID,
    "elementId": ELEMENT_ID
})
if clear_result.get("success"):
    print("  Override cleared")
else:
    print(f"  Note: {clear_result.get('error', 'Could not clear override')}")

# Step 3: Create the RED text note (first line)
print("\nStep 3: Creating RED text note...")
red_result = call_mcp("createTextNote", {
    "viewId": VIEW_ID,
    "text": RED_TEXT,
    "x": orig_x,
    "y": orig_y,
    "z": orig_z
})

if not red_result.get("success"):
    print(f"ERROR creating red text: {red_result.get('error')}")
    exit(1)

red_id = red_result.get("result", {}).get("id")
print(f"  Created red text element: {red_id}")

# Step 4: Apply RED override to the new text
print("\nStep 4: Applying RED color override...")
override_result = call_mcp("overrideElementGraphics", {
    "viewId": VIEW_ID,
    "elementId": red_id,
    "lineColor": {"r": 255, "g": 0, "b": 0}
})

if override_result.get("success"):
    print("  RED override applied!")
else:
    print(f"  ERROR: {override_result.get('error')}")

# Step 5: Create the BLACK text note (remaining lines)
# Position it below the red text (adjust Y coordinate)
# Typical text height offset in Revit feet (about 0.5 feet = 6 inches)
y_offset = -0.15  # Negative because Y goes down in view coordinates

print("\nStep 5: Creating BLACK text note...")
black_result = call_mcp("createTextNote", {
    "viewId": VIEW_ID,
    "text": BLACK_TEXT,
    "x": orig_x,
    "y": orig_y + y_offset,
    "z": orig_z
})

if not black_result.get("success"):
    print(f"ERROR creating black text: {black_result.get('error')}")
else:
    black_id = black_result.get("result", {}).get("id")
    print(f"  Created black text element: {black_id}")

# Step 6: Delete the original combined text
print("\nStep 6: Deleting original combined text...")
delete_result = call_mcp("deleteTextNote", {
    "elementId": ELEMENT_ID
})

if delete_result.get("success"):
    print("  Original text deleted!")
else:
    print(f"  ERROR: {delete_result.get('error')}")

print("\n" + "=" * 60)
print("DONE! Check your Revit view.")
print("You should now have:")
print("  - First line in RED")
print("  - Remaining lines in BLACK")
print("=" * 60)
