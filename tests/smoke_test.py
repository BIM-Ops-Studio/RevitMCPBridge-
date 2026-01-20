"""
RevitMCPBridge2026 - Smoke Test
Quick validation that the MCP server is running and responsive

Run this immediately after:
1. Building the project
2. Starting Revit
3. Opening a project/family

This test requires NO specific IDs from your project - it only tests basic connectivity
and read-only operations.
"""

import json
import win32pipe
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def connect_to_server():
    """Connect to the MCP server named pipe"""
    try:
        pipe = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        return pipe
    except pywintypes.error as e:
        return None

def send_command(pipe, method, params):
    """Send a command to the MCP server and get the response"""
    try:
        command = json.dumps({"method": method, "params": params})
        win32file.WriteFile(pipe, command.encode())

        result_bytes = win32file.ReadFile(pipe, 65536)[1]
        result = json.loads(result_bytes.decode())

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_connection():
    """Test 1: Can we connect to the server?"""
    print("\n1. Testing connection to MCP server...")
    print(f"   Pipe name: {PIPE_NAME}")

    pipe = connect_to_server()
    if pipe is None:
        print("   ✗ FAILED: Cannot connect to server")
        print("\n   Troubleshooting:")
        print("   - Is Revit 2026 running?")
        print("   - Is a project or family file open in Revit?")
        print("   - Is the RevitMCPBridge2026 add-in loaded?")
        print("   - Check Revit Add-ins tab for 'MCP Bridge' button")
        print("   - Check: C:\\Users\\rick\\AppData\\Roaming\\Autodesk\\Revit\\Addins\\2026\\")
        return None

    print("   ✓ Connected successfully!")
    return pipe

def test_get_all_views(pipe):
    """Test 2: Can we retrieve views from the project?"""
    print("\n2. Testing getAllViews method...")

    result = send_command(pipe, "getAllViews", {})

    if not result.get("success"):
        print(f"   ✗ FAILED: {result.get('error', 'Unknown error')}")
        return False

    views = result.get("views", [])
    print(f"   ✓ Success! Found {len(views)} views in project")

    # Show first 5 views as sample
    if views:
        print("\n   Sample views:")
        for i, view in enumerate(views[:5]):
            view_name = view.get("name", "Unknown")
            view_type = view.get("viewType", "Unknown")
            view_id = view.get("viewId", "?")
            print(f"   - {view_name} ({view_type}) [ID: {view_id}]")

        if len(views) > 5:
            print(f"   ... and {len(views) - 5} more views")

    return True

def test_get_all_levels(pipe):
    """Test 3: Can we retrieve levels from the project?"""
    print("\n3. Testing getAllLevels method...")

    result = send_command(pipe, "getAllLevels", {})

    if not result.get("success"):
        print(f"   ✗ FAILED: {result.get('error', 'Unknown error')}")
        return False

    levels = result.get("levels", [])
    print(f"   ✓ Success! Found {len(levels)} levels in project")

    if levels:
        print("\n   Levels:")
        for level in levels:
            level_name = level.get("name", "Unknown")
            elevation = level.get("elevation", 0)
            level_id = level.get("levelId", "?")
            print(f"   - {level_name}: {elevation:.2f}' [ID: {level_id}]")

    return True

def test_get_project_info(pipe):
    """Test 4: Can we get project information?"""
    print("\n4. Testing getProjectInfo method...")

    result = send_command(pipe, "getProjectInfo", {})

    if not result.get("success"):
        print(f"   ✗ FAILED: {result.get('error', 'Unknown error')}")
        return False

    print("   ✓ Success! Project information retrieved")
    print(f"\n   Project Name: {result.get('projectName', 'N/A')}")
    print(f"   Project Number: {result.get('projectNumber', 'N/A')}")
    print(f"   Client Name: {result.get('clientName', 'N/A')}")
    print(f"   Project Address: {result.get('projectAddress', 'N/A')}")

    return True

def test_error_handling(pipe):
    """Test 5: Does the server handle errors gracefully?"""
    print("\n5. Testing error handling...")

    # Try to get info for non-existent wall
    result = send_command(pipe, "getWallInfo", {"wallId": 999999999})

    if result.get("success"):
        print("   ✗ UNEXPECTED: Server returned success for invalid wall ID")
        return False

    error_msg = result.get("error", "")
    if error_msg:
        print(f"   ✓ Success! Server properly returned error: '{error_msg}'")
        return True
    else:
        print("   ✗ FAILED: Error response missing error message")
        return False

def main():
    """Run all smoke tests"""
    print_header("RevitMCPBridge2026 - SMOKE TEST")
    print("This test validates basic MCP server functionality")
    print("All tests are read-only - no modifications will be made to your project")

    # Test 1: Connection
    pipe = test_connection()
    if pipe is None:
        print("\n" + "=" * 80)
        print("SMOKE TEST FAILED: Cannot connect to server")
        print("=" * 80)
        return

    # Test 2: Get Views
    test2_passed = test_get_all_views(pipe)

    # Test 3: Get Levels
    test3_passed = test_get_all_levels(pipe)

    # Test 4: Get Project Info
    test4_passed = test_get_project_info(pipe)

    # Test 5: Error Handling
    test5_passed = test_error_handling(pipe)

    # Summary
    print_header("SMOKE TEST SUMMARY")

    tests = [
        ("Connection to server", pipe is not None),
        ("Get all views", test2_passed),
        ("Get all levels", test3_passed),
        ("Get project info", test4_passed),
        ("Error handling", test5_passed)
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    print(f"\nResults: {passed}/{total} tests passed")
    print("")
    for test_name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 80)
    if passed == total:
        print("✓ ALL SMOKE TESTS PASSED!")
        print("The MCP server is operational and ready for use.")
    else:
        print("✗ SOME TESTS FAILED")
        print("Review the output above for details on what went wrong.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
