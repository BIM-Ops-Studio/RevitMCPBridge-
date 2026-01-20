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

print("=" * 60)
print("REVIT MCP BRIDGE - SYSTEM VERIFICATION")
print("=" * 60)

# Test 1: Basic connectivity
print("\n1. Testing basic connectivity (ping)...")
result = call_mcp("ping")
if result.get("success"):
    print("   OK - Server responding")
else:
    print(f"   FAIL - Error: {result.get('error')}")

# Test 2: Get levels (tests FloorCeilingRoofMethods)
print("\n2. Testing getLevels (FloorCeilingRoofMethods)...")
result = call_mcp("getLevels")
if result.get("success"):
    levels = result.get("result", {}).get("levels", [])
    print(f"   OK - Found {len(levels)} levels")
    for lvl in levels[:3]:
        print(f"      - {lvl.get('name')}: {lvl.get('elevation'):.2f} ft")
else:
    print(f"   FAIL - Error: {result.get('error')}")

# Test 3: Get grids (tests ProjectSetupMethods)
print("\n3. Testing getGrids (ProjectSetupMethods)...")
result = call_mcp("getGrids")
if result.get("success"):
    grids = result.get("result", {}).get("grids", [])
    print(f"   OK - Found {len(grids)} grids")
else:
    print(f"   FAIL - Error: {result.get('error')}")

# Test 4: Get wall types (tests WallMethods)
print("\n4. Testing getWallTypes (WallMethods)...")
result = call_mcp("getWallTypes")
if result.get("success"):
    types = result.get("result", {}).get("wallTypes", [])
    print(f"   OK - Found {len(types)} wall types")
else:
    print(f"   FAIL - Error: {result.get('error')}")

# Test 5: Get floor types (tests new methods)
print("\n5. Testing getFloorTypes (FloorCeilingRoofMethods)...")
result = call_mcp("getFloorTypes")
if result.get("success"):
    types = result.get("result", {}).get("floorTypes", [])
    print(f"   OK - Found {len(types)} floor types")
else:
    print(f"   FAIL - Error: {result.get('error')}")

# Test 6: Get project info
print("\n6. Testing getProjectInfo...")
result = call_mcp("getProjectInfo")
if result.get("success"):
    info = result.get("result", {})
    print(f"   OK - Project: {info.get('projectName', 'N/A')}")
else:
    print(f"   FAIL - Error: {result.get('error')}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
