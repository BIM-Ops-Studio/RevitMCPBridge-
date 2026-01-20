# RevitMCPBridge2026 - Test Suite

This directory contains test scripts for validating the MCP server functionality.

## Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install pywin32
   ```

2. **Revit must be running** with a project or family file open

3. **MCP server add-in must be loaded** in Revit
   - Check: Revit → Add-ins tab → Should see "MCP Bridge" button
   - DLL location: `C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\`

## Test Files

### 1. smoke_test.py - Quick Validation ⚡
**Purpose:** Verify basic server connectivity and functionality
**Requirements:** None - uses read-only operations
**Run first:** Always run this before other tests
**Usage:**
```bash
cd /mnt/d/RevitMCPBridge2026/tests
python3 smoke_test.py
```

**What it tests:**
- Connection to named pipe
- Get all views
- Get all levels
- Get project info
- Error handling

### 2. test_wall_methods.py - Wall Operations 🧱
**Purpose:** Test all wall-related MCP methods
**Requirements:** You must configure TEST_DATA with IDs from your project
**Usage:**
```bash
python3 test_wall_methods.py
```

**What it tests:**
- Create wall by points
- Get wall information
- Modify wall parameters
- Get wall location
- Flip wall orientation
- Delete wall
- Get all walls
- Get wall types

**Before running:**
1. Run the script once - it will show you how to get IDs
2. Open Revit Python Shell or Dynamo
3. Run the helper code to get IDs
4. Update `TEST_DATA` in the script
5. Run again

## Running Tests

### Quick Start (Smoke Test Only)
```bash
# From WSL
cd /mnt/d/RevitMCPBridge2026/tests
python3 smoke_test.py
```

### Full Test Suite (When ready)
```bash
# 1. Smoke test first
python3 smoke_test.py

# 2. Configure and run wall tests
python3 test_wall_methods.py

# Future: Additional test files will go here
```

## Getting Test IDs from Revit

Many tests require element IDs from your specific project. Here's how to get them:

### Method 1: Revit Python Shell
1. Install Revit Python Shell (if not installed)
2. Open your Revit project
3. Run the code snippets shown in test scripts

### Method 2: Dynamo
1. Open Dynamo in Revit
2. Use code blocks to run Python
3. Copy the IDs output

### Method 3: From MCP Server Directly
Use the smoke test or simple queries to discover IDs:
```python
# Example: Get wall type IDs
import json
import win32file

pipe = win32file.CreateFile(
    r'\\.\pipe\RevitMCPBridge2026',
    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
    0, None,
    win32file.OPEN_EXISTING,
    0, None
)

command = json.dumps({"method": "getWallTypes", "params": {}})
win32file.WriteFile(pipe, command.encode())
result = json.loads(win32file.ReadFile(pipe, 65536)[1].decode())
print(json.dumps(result, indent=2))
```

## Test Development Guidelines

When creating new test scripts, follow these patterns:

### 1. File Naming
- `test_<category>_methods.py` - For specific method categories
- `test_<workflow>_integration.py` - For integration/workflow tests
- `smoke_test.py` - Quick validation tests

### 2. Script Structure
```python
# Imports
import json
import win32file
# ... other imports

# Constants
PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

# Test data (if needed)
TEST_DATA = {
    "someId": None,  # User must configure
}

# Helper functions
def connect():
    """Connect to server"""
    pass

def send_command(pipe, method, params):
    """Send command"""
    pass

# Test functions
def test_something(pipe):
    """Test: Description"""
    print_test("methodName")
    # ... test code ...
    return True/False

# Main runner
def main():
    """Run all tests"""
    # Connect
    # Run tests
    # Print summary
    pass

if __name__ == "__main__":
    main()
```

### 3. Test Function Pattern
```python
def test_method_name(pipe, *args):
    """Test: Short description of what is being tested"""
    print_test("methodName")  # Clear output

    # Skip if prerequisites not met
    if not required_data:
        print("✗ SKIPPED: Missing required data")
        return None

    # Prepare test parameters
    params = {
        "param1": value1,
        "param2": value2,
    }

    # Execute test
    result = send_command(pipe, "methodName", params)

    # Verify result
    if not result.get("success"):
        print(f"✗ FAILED: {result.get('error')}")
        return False

    # Validate response data
    print("✓ Success! Description of what passed")
    # ... print relevant info ...

    return True
```

### 4. Error Handling Test Pattern
Always include error handling tests:
```python
def test_error_handling(pipe):
    """Test: Verify server handles errors gracefully"""

    # Test 1: Invalid ID
    result = send_command(pipe, "getElement", {"elementId": 999999999})
    assert not result.get("success"), "Should fail for invalid ID"
    assert "error" in result, "Should return error message"

    # Test 2: Missing parameter
    result = send_command(pipe, "createElement", {})
    assert not result.get("success"), "Should fail for missing params"

    # Test 3: Invalid parameter type
    result = send_command(pipe, "setParameter", {"value": "not-a-number"})
    assert not result.get("success"), "Should fail for wrong type"

    return True
```

## Troubleshooting

### Cannot connect to server
```
Error: "The system cannot find the file specified"
```
**Solutions:**
1. Check Revit is running
2. Check a project/family is open
3. Restart Revit to reload add-in
4. Verify DLL is in correct location
5. Check Revit version (must be 2026)

### Tests fail with "Not yet implemented"
This is expected for framework methods. Check `MCP_SERVER_ARCHITECTURE.md` for implementation status.

### Transaction errors
```
Error: "Cannot start transaction - another transaction is active"
```
**Solution:** Ensure no other operations are running in Revit. Close any open transaction dialogs.

### Permission errors on Windows
If running from WSL and getting permission errors:
```bash
# Run with Windows Python instead
cd /mnt/d/RevitMCPBridge2026/tests
/mnt/c/Python39/python.exe smoke_test.py
```

## Test Results Tracking

Create a test log to track results over time:

```bash
# Run tests and save results
python3 smoke_test.py > test_results_$(date +%Y%m%d_%H%M%S).log 2>&1
```

## CI/CD Integration (Future)

These tests can be automated with:
1. Revit must be running (can be automated with Revit Server)
2. Test project must be open
3. Run tests via Python
4. Parse output for pass/fail

Example:
```bash
#!/bin/bash
# Start Revit with test project
# Wait for Revit to load
# Run smoke test
# If smoke test passes, run full suite
# Collect results
# Close Revit
```

## Contributing Tests

When adding new tests:

1. Follow naming conventions
2. Include clear docstrings
3. Handle errors gracefully
4. Print clear success/failure messages
5. Clean up test data (delete created elements)
6. Update this README with new test info

## Related Documentation

- `../TESTING_FRAMEWORK.md` - Overall testing strategy
- `../METHOD_VALIDATION_CHECKLIST.md` - Method validation requirements
- `../MCP_SERVER_ARCHITECTURE.md` - Complete method inventory

---

**Last Updated:** 2025-01-13
**Version:** 1.0.0
