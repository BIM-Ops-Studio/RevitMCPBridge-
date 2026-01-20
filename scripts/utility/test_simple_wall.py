#!/usr/bin/env python3
"""Simple test to create one wall via MCP"""

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

def send_mcp_request(method, params):
    """Send a request to the MCP server and return the response"""
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )

        request = {
            "method": method,
            "params": params
        }
        request_json = json.dumps(request) + "\n"
        print(f">>> Sending: {request_json[:200]}...")

        win32file.WriteFile(handle, request_json.encode('utf-8'))
        result, data = win32file.ReadFile(handle, 64 * 1024)
        win32file.CloseHandle(handle)

        response = data.decode('utf-8')
        print(f"<<< Response length: {len(response)} chars")
        print(f"<<< First 500 chars: {response[:500]}")

        return json.loads(response)
    except pywintypes.error as e:
        if e.args[0] == 2:
            return {"success": False, "error": "MCP Server not running."}
        return {"success": False, "error": f"Pipe error: {e}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON decode error: {e}", "raw_response": response[:1000] if response else "empty"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Test 1: Get Levels
print("\n=== TEST 1: getLevels ===")
levels = send_mcp_request("getLevels", {})
print(f"Result: {levels}")

level_id = None
if levels.get("success"):
    level_list = levels.get("levels", [])
    if level_list:
        level_id = level_list[0].get("levelId")
        print(f"Using level ID: {level_id}")

# Test 2: Get Wall Types (with larger buffer)
print("\n=== TEST 2: getWallTypes ===")
wall_types = send_mcp_request("getWallTypes", {})
print(f"Result success: {wall_types.get('success')}")
if wall_types.get('success'):
    type_list = wall_types.get("wallTypes", [])
    print(f"Found {len(type_list)} wall types")
    if type_list:
        print(f"First wall type: {type_list[0]}")
        wall_type_id = type_list[0].get("wallTypeId")
        print(f"Using wall type ID: {wall_type_id}")

# Test 3: Create single wall
if level_id:
    print("\n=== TEST 3: createWallByPoints ===")
    wall_params = {
        "startPoint": [0, 0, 0],
        "endPoint": [10, 0, 0],
        "levelId": level_id,
        "height": 10.0
    }
    result = send_mcp_request("createWallByPoints", wall_params)
    print(f"Result: {result}")

print("\n=== TESTS COMPLETE ===")
