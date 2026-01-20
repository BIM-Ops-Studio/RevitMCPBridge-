#!/usr/bin/env python3
"""Quick test of Sheet Pattern methods"""

import json
import win32pipe
import win32file

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def test_method(method, parameters):
    """Test a single MCP method"""
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

        response = json.loads(data.decode('utf-8'))
        return response
    except Exception as e:
        return {"success": False, "error": str(e)}

print("Testing Sheet Pattern Methods...")
print("=" * 80)

# Test 1: List Known Firms (doesn't need Revit data)
print("\n1. Testing listKnownFirms...")
result = test_method("listKnownFirms", {})
print(json.dumps(result, indent=2))

# Test 2: Get Pattern Rules for Pattern C
print("\n2. Testing getPatternRules for Pattern C...")
result = test_method("getPatternRules", {"patternId": "C"})
print(json.dumps(result, indent=2))

# Test 3: Generate Floor Plan Sheets
print("\n3. Testing generateFloorPlanSheets...")
result = test_method("generateFloorPlanSheets", {
    "patternId": "A",
    "floorCount": 4,
    "buildingNumber": 1
})
print(json.dumps(result, indent=2))

print("\n" + "=" * 80)
print("Quick test complete!")
