#!/usr/bin/env python3
"""Flexible Sheet Pattern Generator - Fast and User-Controlled"""

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

print("=" * 80)
print("  FLEXIBLE SHEET PATTERN GENERATOR")
print("=" * 80)

# STEP 1: Try to detect pattern from existing sheets (quick, no firm lookup)
print("\nAnalyzing existing sheets...")
detect_result = send_mcp_request("detectExistingPattern", {})

suggested_pattern = "C"  # Default to Pattern C (most common)

if detect_result.get("success"):
    detected = detect_result.get("detectedPattern", "C")
    confidence = detect_result.get("confidence", "low")
    print(f"  Detected Pattern: {detected} (Confidence: {confidence})")
    if confidence in ["high", "medium"]:
        suggested_pattern = detected
else:
    print("  No existing sheets found - will use default")

# STEP 2: Show available patterns
print("\n" + "-" * 80)
print("AVAILABLE PATTERNS:")
print("-" * 80)
patterns = [
    ("A", "Hyphen-Decimal (A-1.1, A-1.2) - Hugh Anglin, Raymond Hall"),
    ("C", "Three-Digit Sequential (A101, A102) - Professional Standard"),
    ("C-Zero", "Zero-Based Cover (A000, A101) - Bluebeam Users"),
    ("C-Institutional", "G-Prefix with Bid Alternates (G001, A101.1) - Vines Architecture"),
    ("D", "Space-Decimal (A 0.0, A2.1) - Fantal Consulting")
]

for i, (pattern_id, description) in enumerate(patterns, 1):
    marker = " <-- SUGGESTED" if pattern_id == suggested_pattern else ""
    print(f"  {i}. Pattern {pattern_id}: {description}{marker}")

# STEP 3: Get user choice
print("\n" + "-" * 80)
choice = input(f"Select pattern (1-5) or press Enter for suggested [{suggested_pattern}]: ").strip()

pattern_map = {
    "1": "A",
    "2": "C",
    "3": "C-Zero",
    "4": "C-Institutional",
    "5": "D",
    "": suggested_pattern
}

selected_pattern = pattern_map.get(choice, suggested_pattern)
print(f"\n>>> Using Pattern {selected_pattern}")

# STEP 4: Get project parameters
print("\n" + "-" * 80)
print("PROJECT SETUP:")
print("-" * 80)

floor_count = input("Number of floors (default: 4): ").strip()
floor_count = int(floor_count) if floor_count.isdigit() else 4

building_count = input("Number of buildings (default: 1): ").strip()
building_count = int(building_count) if building_count.isdigit() else 1

has_rcp = input("Include RCP sheets? (y/n, default: y): ").strip().lower() != 'n'
has_sections = input("Include sections? (y/n, default: y): ").strip().lower() != 'n'
has_details = input("Include details? (y/n, default: y): ").strip().lower() != 'n'
has_schedules = input("Include schedules? (y/n, default: y): ").strip().lower() != 'n'

# STEP 5: Generate complete sheet set
print("\n" + "=" * 80)
print("GENERATING SHEET SET...")
print("=" * 80)

result = send_mcp_request("generateCompleteSheetSet", {
    "patternId": selected_pattern,
    "floorCount": floor_count,
    "buildingCount": building_count,
    "hasRCP": has_rcp,
    "hasSections": has_sections,
    "hasDetails": has_details,
    "hasSchedules": has_schedules
})

if result.get("success"):
    sheets = result.get("sheets", [])
    sheet_count = result.get("sheetCount", 0)

    print(f"\n>>> Generated {sheet_count} sheets using Pattern {selected_pattern}")
    print("\nSheet List:")
    print("-" * 80)

    for i, sheet in enumerate(sheets, 1):
        number = sheet.get('number', 'N/A')
        name = sheet.get('name', 'Unnamed')
        print(f"  {i:2d}. {number:12s} - {name}")

    # STEP 6: Ask if user wants to create them
    print("\n" + "=" * 80)
    create = input("\nCreate these sheets in Revit? (y/n): ").strip().lower()

    if create == 'y':
        print("\nCreating sheets in Revit...")

        # Extract sheet list for creation
        sheet_list = [{"number": s.get("number"), "name": s.get("name")} for s in sheets]

        create_result = send_mcp_request("createSheetsFromPattern", {
            "patternId": selected_pattern,
            "sheetList": sheet_list
        })

        if create_result.get("success"):
            created = create_result.get("createdSheets", [])
            print(f"\n>>> SUCCESS: Created {len(created)} sheets in Revit!")

            # Save pattern to client profile for future use
            print("\nSaving pattern preference...")
            send_mcp_request("createClientProfile", {
                "firmName": "User Selected",
                "patternId": selected_pattern,
                "preferences": {
                    "floorCount": floor_count,
                    "buildingCount": building_count,
                    "hasRCP": has_rcp,
                    "hasSections": has_sections,
                    "hasDetails": has_details,
                    "hasSchedules": has_schedules
                }
            })
            print("  Pattern preference saved for next time!")
        else:
            print(f"\n>>> ERROR: {create_result.get('error', 'Unknown error')}")
    else:
        print("\nSheet creation cancelled. You can run this again anytime.")
        print("\nTIP: You can also change patterns later using 'convertBetweenPatterns'")
else:
    print(f"\n>>> ERROR: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 80)
print("Done!")
print("=" * 80)
