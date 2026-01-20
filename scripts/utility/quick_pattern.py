#!/usr/bin/env python3
"""Quick Pattern Selection - No Detection, Just Pick and Go"""

import json
import sys
import win32pipe
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, parameters):
    """Send request to MCP server"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        request = json.dumps({"method": method, "parameters": parameters})
        win32file.WriteFile(handle, request.encode('utf-8'))
        result, data = win32file.ReadFile(handle, 64 * 1024)
        win32file.CloseHandle(handle)
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        return {"success": False, "error": str(e)}

# Check for command-line pattern argument
if len(sys.argv) > 1:
    pattern_arg = sys.argv[1].upper()
    # Map pattern names
    if pattern_arg in ["A", "C", "C-ZERO", "C-INSTITUTIONAL", "D"]:
        selected_pattern = pattern_arg
        if pattern_arg == "C-ZERO":
            selected_pattern = "C-Zero"
        elif pattern_arg == "C-INSTITUTIONAL":
            selected_pattern = "C-Institutional"
    else:
        print(f"Unknown pattern: {pattern_arg}")
        print("Usage: python quick_pattern.py [A|C|C-Zero|C-Institutional|D] [floors]")
        sys.exit(1)

    # Get floor count if provided
    floor_count = 4
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        floor_count = int(sys.argv[2])

    print(f"Quick Generate: Pattern {selected_pattern}, {floor_count} floors")

    # Generate and show preview
    result = send_mcp_request("generateCompleteSheetSet", {
        "patternId": selected_pattern,
        "floorCount": floor_count,
        "buildingCount": 1,
        "hasRCP": True,
        "hasSections": True,
        "hasDetails": True,
        "hasSchedules": True
    })

    if result.get("success"):
        sheets = result.get("sheets", [])
        print(f"\nGenerated {len(sheets)} sheets:\n")
        for sheet in sheets:
            print(f"  {sheet.get('number'):12s} - {sheet.get('name')}")
        print(f"\nTo create: Add 'create' argument")
        print(f"Example: python quick_pattern.py {selected_pattern} {floor_count} create")
    else:
        print(f"Error: {result.get('error')}")
    sys.exit(0)

# Interactive mode
print("QUICK PATTERN SELECTOR")
print("=" * 60)
print("1. Pattern A - Hyphen-Decimal (A-1.1)")
print("2. Pattern C - Sequential (A101) [DEFAULT]")
print("3. Pattern C-Zero - Zero-based (A000)")
print("4. Pattern C-Institutional - G-prefix (G001)")
print("5. Pattern D - Space-Decimal (A 2.1)")
print("=" * 60)

choice = input("Pick (1-5) or Enter for C: ").strip()
patterns = {"1": "A", "2": "C", "3": "C-Zero", "4": "C-Institutional", "5": "D", "": "C"}
pattern = patterns.get(choice, "C")

floors = input("Floors (default 4): ").strip()
floors = int(floors) if floors.isdigit() else 4

print(f"\nPattern {pattern}, {floors} floors")

result = send_mcp_request("generateFloorPlanSheets", {
    "patternId": pattern,
    "floorCount": floors,
    "buildingNumber": 1
})

if result.get("success"):
    sheets = result.get("sheetNumbers", [])
    print("\nFloor Plan Sheets:")
    for s in sheets:
        print(f"  {s}")
else:
    print(f"Error: {result.get('error')}")
