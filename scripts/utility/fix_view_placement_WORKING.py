"""
FIXED VERSION - Complete Sheet Creation with View Placement
Now using correct response structures from getViews and getAllSheets
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def get_view_id_by_name_FIXED(client, view_name):
    """Get view ElementId by name - FIXED VERSION"""
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"      [ERROR] getViews failed: {result.get('error')}")
        return None

    # FIXED: Views are in result.result.views, not result.views!
    views_data = result.get("result", {})
    views = views_data.get("views", [])

    print(f"      [DEBUG] Found {len(views)} total views in project")

    for view in views:
        if view.get("name") == view_name:
            view_id = view.get("id")
            print(f"      [SUCCESS] Found view '{view_name}' with ID: {view_id}")
            return view_id

    print(f"      [WARNING] View '{view_name}' not found in {len(views)} views")
    # Print first few views for debugging
    for i, view in enumerate(views[:5]):
        print(f"         Available view {i+1}: {view.get('name')} (ID: {view.get('id')})")

    return None

def get_sheet_id_by_number_FIXED(client, sheet_number):
    """Get sheet ElementId by sheet number - FIXED VERSION"""
    result = client.send_request("getAllSheets", {})

    if not result.get("success"):
        print(f"      [ERROR] getAllSheets failed: {result.get('error')}")
        return None

    # FIXED: Sheets are directly in result.sheets and use sheetId not id!
    sheets = result.get("sheets", [])

    print(f"      [DEBUG] Found {len(sheets)} total sheets in project")

    for sheet in sheets:
        if sheet.get("sheetNumber") == sheet_number:
            sheet_id = sheet.get("sheetId")
            print(f"      [SUCCESS] Found sheet '{sheet_number}' with ID: {sheet_id}")
            return sheet_id

    print(f"      [WARNING] Sheet '{sheet_number}' not found in {len(sheets)} sheets")
    # Print first few sheets for debugging
    for i, sheet in enumerate(sheets[:5]):
        print(f"         Available sheet {i+1}: {sheet.get('sheetNumber')} (ID: {sheet.get('sheetId')})")

    return None

def create_and_place_floor_plan_WORKING(client):
    """WORKING VERSION - Create complete sheet with view placement"""
    print("\n" + "=" * 80)
    print("FIXED VERSION: CREATING COMPLETE SHEET WITH VIEW PLACED!")
    print("=" * 80)

    # Step 1: Create the floor plan view
    print("\n[STEP 1/5] Creating Level 1 floor plan view...")
    view_result = client.send_request("createFloorPlan", {
        "levelName": "Level 1",
        "viewName": "L1 - WORKING TEST"
    })

    view_name = "L1 - WORKING TEST"
    if view_result.get("success"):
        print(f"      [SUCCESS] Created view: {view_name}")
    else:
        error = view_result.get("error", "")
        if "already exists" in error.lower() or "duplicate" in error.lower():
            print(f"      [INFO] View already exists, using existing: {view_name}")
        else:
            print(f"      [WARNING] Create view response: {error}")

    # Step 2: Get the view ID using FIXED lookup
    print("\n[STEP 2/5] Getting view ElementId (FIXED lookup)...")
    view_id = get_view_id_by_name_FIXED(client, view_name)

    if not view_id:
        print(f"      [ERROR] Could not find view ID - stopping")
        return False

    # Step 3: Create the sheet
    print("\n[STEP 3/5] Creating sheet...")
    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "WORKING-01",
        "sheetName": "COMPLETE SHEET - WORKING VERSION"
    })

    sheet_number = "WORKING-01"
    if sheet_result.get("success"):
        print(f"      [SUCCESS] Created sheet: {sheet_number}")
    else:
        error = sheet_result.get("error", "")
        if "already exists" in error.lower() or "duplicate" in error.lower():
            print(f"      [INFO] Sheet already exists, using existing: {sheet_number}")
        else:
            print(f"      [WARNING] Create sheet response: {error}")

    # Step 4: Get the sheet ID using FIXED lookup
    print("\n[STEP 4/5] Getting sheet ElementId (FIXED lookup)...")
    sheet_id = get_sheet_id_by_number_FIXED(client, sheet_number)

    if not sheet_id:
        print(f"      [ERROR] Could not find sheet ID - stopping")
        return False

    # Step 5: Place view on sheet with proper parameters
    print("\n[STEP 5/5] Placing view on sheet...")
    print(f"      Using sheetId: {sheet_id}")
    print(f"      Using viewId: {view_id}")
    print(f"      Using location: [1.5, 1.0] (feet from origin)")

    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [1.5, 1.0]
    })

    if place_result.get("success"):
        print("\n" + "=" * 80)
        print("*** SUCCESS! VIEW PLACED ON SHEET! ***")
        print("=" * 80)
        print()
        print(f"Sheet: {sheet_number}")
        print(f"View: {view_name}")
        print(f"Status: COMPLETE - View is on the sheet!")
        print()
        return True
    else:
        error = place_result.get("error", "Unknown error")
        print(f"\n      [ERROR] Failed to place view: {error}")
        print(f"      sheetId was: {sheet_id}")
        print(f"      viewId was: {view_id}")

        # Try different coordinates
        print(f"\n      Trying alternative coordinates...")
        for coords in [[0, 0], [1, 1], [2, 1.5]]:
            print(f"         Trying location: {coords}")
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": coords
            })
            if place_result.get("success"):
                print(f"         [SUCCESS] Worked with coordinates: {coords}!")
                return True
            else:
                print(f"         [FAILED] {place_result.get('error')}")

        return False

def main():
    print("\n" + "=" * 80)
    print("FIXED ELEMENT ID LOOKUP CHAIN - TESTING")
    print("=" * 80)
    print()
    print("Changes made:")
    print("  1. FIXED: getViews returns result.result.views")
    print("  2. FIXED: getAllSheets returns result.sheets with sheetId")
    print("  3. FIXED: Proper error handling and debugging")
    print()

    client = RevitClient()

    success = create_and_place_floor_plan_WORKING(client)

    print("\n" + "=" * 80)
    if success:
        print("*** COMPLETE SHEETS WITH VIEWS - WORKING! ***")
        print()
        print("CHECK YOUR REVIT PROJECT:")
        print("  Sheet: WORKING-01")
        print("  Should have: Level 1 floor plan visible on it!")
        print()
        print("The ElementID lookup chain is FIXED!")
        print("I can now autonomously create complete sheets with views!")
    else:
        print("*** FURTHER INVESTIGATION NEEDED ***")
        print()
        print("ElementID lookups are working, but placeViewOnSheet may need:")
        print("  - Different parameter format")
        print("  - Additional validation")
        print("  - Or specific coordinate system")
    print("=" * 80)

if __name__ == "__main__":
    main()
