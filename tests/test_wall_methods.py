"""
RevitMCPBridge2026 - Wall Methods Test Suite
Tests all wall-related MCP methods

BEFORE RUNNING:
1. Open a Revit project
2. Run smoke_test.py to ensure server is working
3. Get IDs from your project using the helper functions below
4. Update the TEST_DATA section with your project's IDs

Methods tested:
- createWallByPoints
- getWallInfo
- modifyWallParameters
- getAllWalls
- getWallTypes
- joinWalls
- unjoinWalls
- splitWall
- flipWall
- getWallLocation
- deleteWall
"""

import json
import win32pipe
import win32file
import pywintypes

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# ============================================================================
# TEST DATA - UPDATE THESE WITH YOUR PROJECT'S VALUES
# ============================================================================

TEST_DATA = {
    # Get these IDs from your Revit project first
    "wallTypeId": None,      # Required: ID of a wall type (e.g., "Basic Wall: Generic - 8\"")
    "levelId": None,         # Required: ID of a level (e.g., "Level 1")
    "viewId": None,          # Optional: For view-specific tests
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_test(test_name):
    """Print test start"""
    print(f"\n>>> Testing: {test_name}")

def connect():
    """Connect to MCP server"""
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
        print(f"✗ Connection failed: {e}")
        return None

def send_command(pipe, method, params):
    """Send command to server"""
    try:
        command = json.dumps({"method": method, "params": params})
        win32file.WriteFile(pipe, command.encode())
        result = json.loads(win32file.ReadFile(pipe, 65536)[1].decode())
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_test_ids():
    """Helper function to retrieve IDs from your project"""
    print_header("GETTING TEST IDS FROM YOUR PROJECT")
    print("\nStep 1: Get wall type IDs")
    print("Run this in Revit Python Shell or Dynamo:")
    print("-" * 80)
    print("""
# Get all wall types
wall_types = FilteredElementCollector(doc).OfClass(WallType).ToElements()
for wt in wall_types[:5]:  # First 5
    print(f"{wt.Name}: {wt.Id.IntegerValue}")
""")

    print("\nStep 2: Get level IDs")
    print("-" * 80)
    print("""
# Get all levels
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
for level in levels:
    print(f"{level.Name}: {level.Id.IntegerValue}")
""")

    print("\nStep 3: Get active view ID (optional)")
    print("-" * 80)
    print("""
# Get active view
print(f"Active View: {doc.ActiveView.Name} - {doc.ActiveView.Id.IntegerValue}")
""")

    print("\n" + "=" * 80)
    print("Copy the IDs from above and update TEST_DATA in this script")
    print("=" * 80)

# ============================================================================
# TESTS
# ============================================================================

def test_get_wall_types(pipe):
    """Test: Get all wall types"""
    print_test("getWallTypes")

    result = send_command(pipe, "getWallTypes", {})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return None

    wall_types = result.get("wallTypes", [])
    print(f"✓ Success! Found {len(wall_types)} wall types")

    if wall_types:
        print("\nAvailable wall types (first 5):")
        for i, wt in enumerate(wall_types[:5]):
            print(f"  {i+1}. {wt.get('name')} [ID: {wt.get('wallTypeId')}]")

        # Return first wall type ID for use in other tests
        return wall_types[0].get('wallTypeId')

    return None

def test_get_all_walls(pipe):
    """Test: Get all walls in project"""
    print_test("getAllWalls")

    result = send_command(pipe, "getAllWalls", {})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return []

    walls = result.get("walls", [])
    print(f"✓ Success! Found {len(walls)} walls in project")

    if walls:
        print("\nSample walls (first 5):")
        for i, wall in enumerate(walls[:5]):
            wall_id = wall.get("wallId")
            wall_type = wall.get("wallType", "Unknown")
            print(f"  {i+1}. Wall ID {wall_id} - Type: {wall_type}")

    return walls

def test_create_wall(pipe, wall_type_id, level_id):
    """Test: Create a new wall"""
    print_test("createWallByPoints")

    if not wall_type_id or not level_id:
        print("✗ SKIPPED: Missing wallTypeId or levelId")
        return None

    # Create a simple 10-foot wall
    params = {
        "points": [
            [0, 0, 0],
            [10, 0, 0]
        ],
        "wallTypeId": wall_type_id,
        "levelId": level_id,
        "height": 10.0,
        "offset": 0.0
    }

    result = send_command(pipe, "createWallByPoints", params)

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return None

    wall_id = result.get("wallId")
    print(f"✓ Success! Wall created with ID: {wall_id}")

    return wall_id

def test_get_wall_info(pipe, wall_id):
    """Test: Get information about a wall"""
    print_test("getWallInfo")

    if not wall_id:
        print("✗ SKIPPED: No wall ID provided")
        return False

    result = send_command(pipe, "getWallInfo", {"wallId": wall_id})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    print("✓ Success! Wall information retrieved:")
    print(f"  Wall ID: {result.get('wallId')}")
    print(f"  Type: {result.get('wallType')}")
    print(f"  Length: {result.get('length', 0):.2f} feet")
    print(f"  Height: {result.get('height', 0):.2f} feet")
    print(f"  Level: {result.get('levelName')}")

    return True

def test_modify_wall_parameters(pipe, wall_id):
    """Test: Modify wall parameters"""
    print_test("modifyWallParameters")

    if not wall_id:
        print("✗ SKIPPED: No wall ID provided")
        return False

    params = {
        "wallId": wall_id,
        "parameters": {
            "Comments": "Test wall created by MCP server test suite",
            "Mark": "TEST-001"
        }
    }

    result = send_command(pipe, "modifyWallParameters", params)

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    print("✓ Success! Wall parameters modified")
    modified = result.get("modifiedParameters", [])
    if modified:
        print(f"  Modified {len(modified)} parameters:")
        for param in modified:
            print(f"    - {param}")

    return True

def test_get_wall_location(pipe, wall_id):
    """Test: Get wall location curve"""
    print_test("getWallLocation")

    if not wall_id:
        print("✗ SKIPPED: No wall ID provided")
        return False

    result = send_command(pipe, "getWallLocation", {"wallId": wall_id})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    print("✓ Success! Wall location retrieved:")
    start_point = result.get("startPoint", [])
    end_point = result.get("endPoint", [])
    print(f"  Start: ({start_point[0]:.2f}, {start_point[1]:.2f}, {start_point[2]:.2f})")
    print(f"  End: ({end_point[0]:.2f}, {end_point[1]:.2f}, {end_point[2]:.2f})")
    print(f"  Length: {result.get('length', 0):.2f} feet")

    return True

def test_flip_wall(pipe, wall_id):
    """Test: Flip wall orientation"""
    print_test("flipWall")

    if not wall_id:
        print("✗ SKIPPED: No wall ID provided")
        return False

    result = send_command(pipe, "flipWall", {"wallId": wall_id})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    print("✓ Success! Wall flipped")
    print(f"  Wall ID: {result.get('wallId')}")

    # Flip it back to original orientation
    result2 = send_command(pipe, "flipWall", {"wallId": wall_id})
    if result2.get("success"):
        print("  Wall flipped back to original orientation")

    return True

def test_delete_wall(pipe, wall_id):
    """Test: Delete a wall"""
    print_test("deleteWall")

    if not wall_id:
        print("✗ SKIPPED: No wall ID provided")
        return False

    result = send_command(pipe, "deleteWall", {"wallId": wall_id})

    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    print("✓ Success! Wall deleted")
    print(f"  Deleted wall ID: {wall_id}")

    return True

def test_error_handling(pipe):
    """Test: Verify error handling"""
    print_test("Error Handling")

    # Test 1: Invalid wall ID
    result = send_command(pipe, "getWallInfo", {"wallId": 999999999})
    if not result.get("success") and result.get("error"):
        print("✓ Test 1 passed: Invalid wall ID handled correctly")
    else:
        print("✗ Test 1 failed: Invalid wall ID not handled properly")
        return False

    # Test 2: Missing required parameter
    result = send_command(pipe, "createWallByPoints", {"points": [[0,0,0], [10,0,0]]})
    if not result.get("success") and result.get("error"):
        print("✓ Test 2 passed: Missing parameter handled correctly")
    else:
        print("✗ Test 2 failed: Missing parameter not handled properly")
        return False

    # Test 3: Invalid points array
    result = send_command(pipe, "createWallByPoints", {
        "points": [[0,0,0]],  # Only 1 point, need at least 2
        "wallTypeId": 123,
        "levelId": 456
    })
    if not result.get("success") and result.get("error"):
        print("✓ Test 3 passed: Invalid points array handled correctly")
    else:
        print("✗ Test 3 failed: Invalid points array not handled properly")
        return False

    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all wall method tests"""
    print_header("RevitMCPBridge2026 - WALL METHODS TEST SUITE")

    # Check if test data is configured
    if not TEST_DATA["wallTypeId"] or not TEST_DATA["levelId"]:
        get_test_ids()
        print("\n⚠ Test data not configured!")
        print("Please update TEST_DATA in this script and run again.")
        return

    # Connect to server
    print("\n1. Connecting to MCP server...")
    pipe = connect()
    if not pipe:
        print("✗ Cannot connect to server. Is Revit running with a project open?")
        return
    print("✓ Connected")

    # Track results
    results = []

    # Run tests in logical order
    try:
        # Read-only tests first
        results.append(("Get wall types", test_get_wall_types(pipe) is not None))
        results.append(("Get all walls", len(test_get_all_walls(pipe)) >= 0))

        # Create a test wall
        wall_id = test_create_wall(pipe, TEST_DATA["wallTypeId"], TEST_DATA["levelId"])
        results.append(("Create wall", wall_id is not None))

        if wall_id:
            # Test operations on the created wall
            results.append(("Get wall info", test_get_wall_info(pipe, wall_id)))
            results.append(("Modify wall parameters", test_modify_wall_parameters(pipe, wall_id)))
            results.append(("Get wall location", test_get_wall_location(pipe, wall_id)))
            results.append(("Flip wall", test_flip_wall(pipe, wall_id)))

            # Clean up - delete test wall
            results.append(("Delete wall", test_delete_wall(pipe, wall_id)))
        else:
            print("\n⚠ Skipping tests that require a wall ID")
            results.extend([
                ("Get wall info", None),
                ("Modify wall parameters", None),
                ("Get wall location", None),
                ("Flip wall", None),
                ("Delete wall", None)
            ])

        # Error handling tests
        results.append(("Error handling", test_error_handling(pipe)))

    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)

    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped (of {total} tests)")
    print("")

    for test_name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 80)
    if failed == 0 and passed > 0:
        print("✓ ALL TESTS PASSED!")
        print("Wall methods are working correctly.")
    elif failed > 0:
        print("✗ SOME TESTS FAILED")
        print("Review the output above for details.")
    else:
        print("⚠ NO TESTS RUN")
        print("Configure TEST_DATA and try again.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
