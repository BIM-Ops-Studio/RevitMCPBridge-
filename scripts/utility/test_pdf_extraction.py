#!/usr/bin/env python3
"""
Test the new PDF/CAD geometry extraction methods.
"""

import json
import sys
import time

try:
    import win32file
    import pywintypes
except ImportError:
    print("ERROR: pywin32 not installed")
    sys.exit(1)

PIPE_NAME = r'\\.\pipe\RevitMCPBridge2026'

def send_mcp_request(method, params):
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        request = {"method": method, "params": params}
        request_json = json.dumps(request) + "\n"
        win32file.WriteFile(handle, request_json.encode('utf-8'))

        response_data = b""
        for _ in range(100):
            try:
                result, chunk = win32file.ReadFile(handle, 65536)
                response_data += chunk
                decoded = response_data.decode('utf-8').strip()
                parsed = json.loads(decoded)
                win32file.CloseHandle(handle)
                return parsed
            except json.JSONDecodeError:
                time.sleep(0.05)
                continue
        win32file.CloseHandle(handle)
        return {"success": False, "error": "Response incomplete"}
    except pywintypes.error as e:
        return {"success": False, "error": f"Pipe error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print("PDF/CAD GEOMETRY EXTRACTION TEST")
print("=" * 80)

# Step 1: Check project
print("\n1. Checking current project...")
result = send_mcp_request("getProjectInfo", {})
if result.get("success"):
    print(f"   Project: {result.get('projectName', 'Unknown')}")
else:
    print(f"   Error: {result.get('error')}")

# Step 2: Check active view
print("\n2. Checking active view...")
result = send_mcp_request("getActiveView", {})
if result.get("success"):
    print(f"   View: {result.get('viewName', 'Unknown')}")
    print(f"   View ID: {result.get('viewId')}")
else:
    print(f"   Error: {result.get('error')}")

# Step 3: Find imported instances
print("\n3. Looking for imported CAD/PDF instances...")
result = send_mcp_request("getImportedInstances", {})
if result.get("success"):
    imports = result.get("imports", [])
    print(f"   Found {len(imports)} import instances")
    for imp in imports:
        print(f"   - ID: {imp.get('elementId')}, Name: {imp.get('name')}")
        if imp.get('boundingBoxMin'):
            print(f"     BBox: ({imp['boundingBoxMin'][0]:.1f}, {imp['boundingBoxMin'][1]:.1f}) to ({imp['boundingBoxMax'][0]:.1f}, {imp['boundingBoxMax'][1]:.1f})")
else:
    print(f"   Error: {result.get('error')}")

# Step 4: Check for walls (to see what's in the model)
print("\n4. Checking existing walls...")
result = send_mcp_request("getWalls", {})
if result.get("success"):
    walls = result.get("walls", [])
    print(f"   Found {len(walls)} walls")

    if walls:
        # Calculate bounding box
        all_x = []
        all_y = []
        for wall in walls:
            start = wall.get("startPoint", {})
            end = wall.get("endPoint", {})
            if isinstance(start, dict):
                all_x.extend([start.get("x", 0), end.get("x", 0)])
                all_y.extend([start.get("y", 0), end.get("y", 0)])

        if all_x:
            print(f"   Wall bounding box:")
            print(f"   X: {min(all_x):.2f} to {max(all_x):.2f}")
            print(f"   Y: {min(all_y):.2f} to {max(all_y):.2f}")
else:
    print(f"   Error: {result.get('error')}")

# Step 5: If we found imports, try to extract geometry from first one
print("\n5. Testing geometry extraction...")
result = send_mcp_request("getImportedInstances", {})
if result.get("success") and result.get("imports"):
    first_import = result["imports"][0]
    import_id = first_import["elementId"]
    print(f"   Extracting geometry from import ID: {import_id}")

    geom_result = send_mcp_request("getImportedLines", {"importId": import_id, "minLength": 1.0})
    if geom_result.get("success"):
        print(f"   Total lines found: {geom_result.get('totalLinesFound')}")
        print(f"   Lines returned: {geom_result.get('linesReturned')}")
        bbox = geom_result.get("boundingBox", {})
        print(f"   Geometry bounding box:")
        print(f"   X: {bbox.get('minX', 0):.2f} to {bbox.get('maxX', 0):.2f} (width: {bbox.get('width', 0):.2f})")
        print(f"   Y: {bbox.get('minY', 0):.2f} to {bbox.get('maxY', 0):.2f} (height: {bbox.get('height', 0):.2f})")

        # Show first few lines
        lines = geom_result.get("lines", [])[:10]
        print(f"\n   First {len(lines)} lines:")
        for i, line in enumerate(lines):
            print(f"   {i+1}. ({line['startX']:.2f}, {line['startY']:.2f}) to ({line['endX']:.2f}, {line['endY']:.2f}) len={line['length']:.2f}")
    else:
        print(f"   Error: {geom_result.get('error')}")
else:
    print("   No imports found - PDF may need to be imported into Revit")
    print("   To import a PDF: Insert tab > Import PDF")

print("\n" + "=" * 80)
