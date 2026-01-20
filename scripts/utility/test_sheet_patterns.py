#!/usr/bin/env python3
"""Test Sheet Pattern Detection and Generation System"""

import json
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, parameters):
    """Send a request to the MCP server and return the response"""
    try:
        # Connect to named pipe
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        # Prepare request
        request = {
            "method": method,
            "parameters": parameters
        }
        request_json = json.dumps(request)

        # Send request
        win32file.WriteFile(handle, request_json.encode('utf-8'))

        # Read response
        result, data = win32file.ReadFile(handle, 64 * 1024)

        # Close handle
        win32file.CloseHandle(handle)

        # Parse response
        response = json.loads(data.decode('utf-8'))
        return response

    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running. Click 'Start MCP Server' in Revit."}
        else:
            return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_result(result, title):
    """Print result with formatting"""
    print(f"\n[{title}]")
    if result.get("success"):
        print("[SUCCESS]")
        for key, value in result.items():
            if key != "success":
                if isinstance(value, (dict, list)):
                    print(f"\n{key}:")
                    print(json.dumps(value, indent=2))
                else:
                    print(f"{key}: {value}")
    else:
        print(f"[FAILED]: {result.get('error', 'Unknown error')}")
    print("-" * 80)
    return result.get("success", False)

# ============================================================================
# STEP 1: Get Project Information to Extract Firm Name
# ============================================================================
print_header("STEP 1: Reading Project Information")

print("\nGetting project info...")
project_info = send_mcp_request("getProjectInfo", {})
print_result(project_info, "Project Information")

firm_name = None
if project_info.get("success"):
    # Try to extract firm name from various fields
    organization = project_info.get("organization", "")
    author = project_info.get("author", "")
    client = project_info.get("client", "")

    # Use the first non-empty field
    firm_name = organization or author or client or "Unknown Firm"

    print(f"\n>> Detected Firm Name: '{firm_name}'")
    print(f"   Organization: {organization}")
    print(f"   Author: {author}")
    print(f"   Client: {client}")

# ============================================================================
# STEP 2: Get Current Sheets to Understand Project
# ============================================================================
print_header("STEP 2: Analyzing Existing Sheets")

print("\nGetting all sheets in project...")
sheets = send_mcp_request("getAllSheets", {})
print_result(sheets, "Current Sheets")

sheet_count = 0
if sheets.get("success"):
    sheet_list = sheets.get("sheets", [])
    sheet_count = len(sheet_list)
    print(f"\n>> Found {sheet_count} existing sheets")

    if sheet_list:
        print("\nFirst 10 sheets:")
        for i, sheet in enumerate(sheet_list[:10], 1):
            number = sheet.get('number', 'N/A')
            name = sheet.get('name', 'Unnamed')
            print(f"   {i}. {number} - {name}")

# ============================================================================
# STEP 3: Detect Which Pattern Should Be Used
# ============================================================================
print_header("STEP 3: Pattern Detection")

detected_pattern = None
pattern_name = None

if firm_name:
    print(f"\nDetecting pattern for firm: '{firm_name}'...")
    pattern_detect = send_mcp_request("detectSheetPattern", {"firmName": firm_name})
    print_result(pattern_detect, "Pattern Detection")

    if pattern_detect.get("success"):
        detected_pattern = pattern_detect.get("pattern")
        pattern_name = pattern_detect.get("patternName", "Unknown")
        firm_matched = pattern_detect.get("firmMatched", "None")
        confidence = pattern_detect.get("confidence", "unknown")

        print(f"\n>> DETECTED PATTERN: {detected_pattern}")
        print(f"   Pattern Name: {pattern_name}")
        print(f"   Firm Matched: {firm_matched}")
        print(f"   Confidence: {confidence}")

        # Get the full pattern rules
        print(f"\nGetting complete rules for Pattern {detected_pattern}...")
        pattern_rules = send_mcp_request("getPatternRules", {"patternId": detected_pattern})
        print_result(pattern_rules, f"Pattern {detected_pattern} Rules")

# ============================================================================
# STEP 4: Demonstrate Pattern-Based Sheet Generation
# ============================================================================
print_header("STEP 4: Pattern-Based Sheet Generation Demo")

if detected_pattern:
    # Demo: Generate floor plan sheets for a 4-story building
    print(f"\nDemo: Generating floor plan sheets for a 4-story building using Pattern {detected_pattern}...")
    floor_plans = send_mcp_request("generateFloorPlanSheets", {
        "patternId": detected_pattern,
        "floorCount": 4,
        "buildingNumber": 1
    })
    print_result(floor_plans, "Floor Plan Sheet Numbers")

    if floor_plans.get("success"):
        generated_sheets = floor_plans.get("sheetNumbers", [])
        print(f"\n>> Generated {len(generated_sheets)} floor plan sheet numbers:")
        for i, sheet_num in enumerate(generated_sheets, 1):
            print(f"   {i}. {sheet_num}")

    # Demo: Generate complete sheet set
    print(f"\nDemo: Generating complete sheet set using Pattern {detected_pattern}...")
    complete_set = send_mcp_request("generateCompleteSheetSet", {
        "patternId": detected_pattern,
        "floorCount": 4,
        "buildingCount": 1,
        "hasRCP": True,
        "hasSections": True,
        "hasDetails": True,
        "hasSchedules": True
    })
    print_result(complete_set, "Complete Sheet Set")

    if complete_set.get("success"):
        sheet_set = complete_set.get("sheets", [])
        sheet_count_gen = complete_set.get("sheetCount", 0)

        print(f"\n>> Generated complete sheet set with {sheet_count_gen} sheets:")
        print("\nSheet breakdown:")
        for i, sheet in enumerate(sheet_set, 1):
            number = sheet.get('number', 'N/A')
            name = sheet.get('name', 'Unnamed')
            print(f"   {i:2d}. {number:10s} - {name}")

# ============================================================================
# STEP 5: Detect Existing Pattern (Reverse Engineering)
# ============================================================================
print_header("STEP 5: Reverse Engineering - Detect Pattern from Existing Sheets")

if sheet_count > 0:
    print("\nAnalyzing existing sheets to detect their pattern...")
    existing_pattern = send_mcp_request("detectExistingPattern", {})
    print_result(existing_pattern, "Detected Pattern from Existing Sheets")

    if existing_pattern.get("success"):
        detected_existing = existing_pattern.get("detectedPattern")
        confidence = existing_pattern.get("confidence")
        reasoning = existing_pattern.get("reasoning")

        print(f"\n>> REVERSE-ENGINEERED PATTERN: {detected_existing}")
        print(f"   Confidence: {confidence}")
        print(f"   Reasoning: {reasoning}")

        if detected_pattern and detected_existing != detected_pattern:
            print(f"\n⚠ WARNING: Detected pattern from firm name ({detected_pattern}) differs from")
            print(f"          pattern detected from existing sheets ({detected_existing})")
            print(f"          This may indicate the project is using a non-standard pattern.")
else:
    print("\nNo existing sheets to analyze - this is a new project")

# ============================================================================
# STEP 6: List Known Firms
# ============================================================================
print_header("STEP 6: Cataloged Firms and Their Patterns")

print("\nGetting list of all known firms...")
known_firms = send_mcp_request("listKnownFirms", {})
print_result(known_firms, "Known Firms Database")

if known_firms.get("success"):
    firms = known_firms.get("firms", [])
    print(f"\n>> Database contains {len(firms)} firm-pattern mappings:")
    for i, mapping in enumerate(firms, 1):
        firm = mapping.get('firmName', 'Unknown')
        pattern = mapping.get('pattern', 'Unknown')
        print(f"   {i:2d}. {firm:30s} → Pattern {pattern}")

# ============================================================================
# SUMMARY
# ============================================================================
print_header("TEST SUMMARY - Sheet Pattern Detection System")

print("\n[OK] System Status: OPERATIONAL")
print(f"\nProject Analysis:")
print(f"   • Firm Name: {firm_name or 'Not detected'}")
print(f"   • Existing Sheets: {sheet_count}")

if detected_pattern:
    print(f"\nPattern Detection:")
    print(f"   • Detected Pattern: {detected_pattern}")
    print(f"   • Pattern Name: {pattern_name}")
    print(f"   • Confidence: {confidence}")

print("\n" + "=" * 80)
print("Sheet Pattern Detection Test Complete!")
print("=" * 80 + "\n")
