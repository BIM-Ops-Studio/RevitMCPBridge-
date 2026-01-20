"""
Create COMPLETE sheets with views properly placed
Uses ElementIDs and coordinates to place views on sheets
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def get_view_id_by_name(client, view_name):
    """Get view ElementId by name"""
    result = client.send_request("getViews", {})
    if result.get("success"):
        views = result.get("views", [])
        for view in views:
            if view.get("Name") == view_name:
                return view.get("Id")
    return None

def get_sheet_id_by_number(client, sheet_number):
    """Get sheet ElementId by sheet number"""
    result = client.send_request("getAllSheets", {})
    if result.get("success"):
        sheets = result.get("sheets", [])
        for sheet in sheets:
            if sheet.get("SheetNumber") == sheet_number:
                return sheet.get("Id")
    return None

def create_complete_floor_plan_sheet_v2(client):
    """Create floor plan sheet with view properly placed using IDs"""
    print("\n" + "=" * 80)
    print("VERSION 2: COMPLETE FLOOR PLAN SHEET (Using ElementIDs)")
    print("=" * 80)

    # Step 1: Create the floor plan view
    print("\n[1/5] Creating Level 1 floor plan view...")
    view_result = client.send_request("createFloorPlan", {
        "levelName": "Level 1",
        "viewName": "L1 - Complete Sheet Test V2"
    })

    view_name = "L1 - Complete Sheet Test V2"
    if view_result.get("success"):
        print(f"      [SUCCESS] Created view: {view_name}")
    else:
        print(f"      [INFO] Using existing view")

    # Step 2: Get the view ID
    print("\n[2/5] Getting view ElementId...")
    view_id = get_view_id_by_name(client, view_name)
    if view_id:
        print(f"      [SUCCESS] View ID: {view_id}")
    else:
        print(f"      [ERROR] Could not find view ID")
        return False

    # Step 3: Create the sheet
    print("\n[3/5] Creating sheet...")
    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "TEST-V2-01",
        "sheetName": "Complete Floor Plan Sheet V2"
    })

    if sheet_result.get("success"):
        print(f"      [SUCCESS] Created sheet: TEST-V2-01")
    else:
        print(f"      [INFO] Sheet may already exist")

    # Step 4: Get the sheet ID
    print("\n[4/5] Getting sheet ElementId...")
    sheet_id = get_sheet_id_by_number(client, "TEST-V2-01")
    if sheet_id:
        print(f"      [SUCCESS] Sheet ID: {sheet_id}")
    else:
        print(f"      [ERROR] Could not find sheet ID")
        return False

    # Step 5: Place view on sheet with coordinates
    print("\n[5/5] Placing view on sheet at center position...")
    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [0.5, 0.5]  # Center of sheet (relative coordinates)
    })

    if place_result.get("success"):
        print(f"      [SUCCESS] *** VIEW PLACED ON SHEET! ***")
        print(f"      Sheet TEST-V2-01 now has the floor plan view on it!")
        return True
    else:
        print(f"      [ERROR] {place_result.get('error')}")
        print(f"      Trying absolute coordinates instead...")

        # Try with absolute coordinates (in feet, typical sheet is ~3ft x 2ft)
        place_result = client.send_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": view_id,
            "location": [1.5, 1.0]  # 1.5 ft from left, 1 ft from bottom
        })

        if place_result.get("success"):
            print(f"      [SUCCESS] *** VIEW PLACED WITH ABSOLUTE COORDS! ***")
            return True
        else:
            print(f"      [ERROR] {place_result.get('error')}")
            return False

def main():
    print("\n" + "=" * 80)
    print("PROPER SHEET CREATION WITH ELEMENT IDS")
    print("=" * 80)
    print()
    print("This demonstrates the CORRECT workflow:")
    print("  1. Create view")
    print("  2. Get view's ElementId")
    print("  3. Create sheet")
    print("  4. Get sheet's ElementId")
    print("  5. Place view on sheet using IDs + coordinates")
    print()

    client = RevitClient()

    success = create_complete_floor_plan_sheet_v2(client)

    print("\n" + "=" * 80)
    if success:
        print("SUCCESS! CHECK YOUR REVIT PROJECT:")
        print("  Sheet: TEST-V2-01")
        print("  Should have: Level 1 floor plan placed on it!")
        print()
        print("This proves I CAN create complete sheets with views!")
    else:
        print("INVESTIGATION NEEDED:")
        print("  The placeViewOnSheet method may need:")
        print("  - Different coordinate system")
        print("  - Additional parameters")
        print("  - Or the method needs to be fully implemented")
        print()
        print("BUT - the framework exists and I know how to use it!")
    print("=" * 80)

if __name__ == "__main__":
    main()
