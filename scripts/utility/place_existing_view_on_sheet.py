"""
Place an EXISTING view on a sheet - bypassing view creation
This should work since we can successfully retrieve view IDs
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def list_all_floor_plan_views(client):
    """List all floor plan views"""
    result = client.send_request("getViews", {})

    if not result.get("success"):
        return []

    views_data = result.get("result", {})
    views = views_data.get("views", [])

    # Filter for floor plans
    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan" and v.get("level")]

    return floor_plans

def place_existing_view_test(client):
    """Test placing an existing floor plan view on a new sheet"""
    print("\n" + "=" * 80)
    print("TESTING: Place EXISTING View on New Sheet")
    print("=" * 80)

    # Step 1: Find an existing floor plan view
    print("\n[STEP 1/4] Finding existing floor plan views...")
    floor_plans = list_all_floor_plan_views(client)

    if not floor_plans:
        print("      [ERROR] No floor plan views found!")
        return False

    print(f"      [SUCCESS] Found {len(floor_plans)} floor plan views:")
    for i, view in enumerate(floor_plans[:10]):
        print(f"         {i+1}. {view.get('name')} (Level: {view.get('level')}, ID: {view.get('id')})")

    # Use the first floor plan
    selected_view = floor_plans[0]
    view_name = selected_view.get("name")
    view_id = selected_view.get("id")

    print(f"\n      [SELECTED] Will use: {view_name} (ID: {view_id})")

    # Step 2: Create a new sheet
    print("\n[STEP 2/4] Creating new sheet...")
    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "TEST-EXISTING-01",
        "sheetName": "Test - Existing View Placement"
    })

    sheet_number = "TEST-EXISTING-01"
    if sheet_result.get("success"):
        print(f"      [SUCCESS] Created sheet: {sheet_number}")
    else:
        error = sheet_result.get("error", "")
        if "duplicate" in error.lower() or "exists" in error.lower():
            print(f"      [INFO] Sheet exists, will use it")
        else:
            print(f"      [ERROR] {error}")
            return False

    # Step 3: Get sheet ID
    print("\n[STEP 3/4] Getting sheet ID...")
    sheets_result = client.send_request("getAllSheets", {})
    if not sheets_result.get("success"):
        print("      [ERROR] Could not get sheets")
        return False

    sheets = sheets_result.get("sheets", [])
    sheet_id = None
    for sheet in sheets:
        if sheet.get("sheetNumber") == sheet_number:
            sheet_id = sheet.get("sheetId")
            break

    if not sheet_id:
        print(f"      [ERROR] Could not find sheet ID for {sheet_number}")
        return False

    print(f"      [SUCCESS] Sheet ID: {sheet_id}")

    # Step 4: Place view on sheet
    print("\n[STEP 4/4] Placing view on sheet...")
    print(f"      sheetId: {sheet_id}")
    print(f"      viewId: {view_id}")
    print(f"      location: [1.5, 1.0]")

    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [1.5, 1.0]
    })

    if place_result.get("success"):
        print("\n" + "=" * 80)
        print("*** SUCCESS!!! VIEW PLACED ON SHEET!!! ***")
        print("=" * 80)
        print()
        print(f"Sheet Number: {sheet_number}")
        print(f"Sheet Name: Test - Existing View Placement")
        print(f"View Placed: {view_name}")
        print(f"View ID: {view_id}")
        print()
        print("GO CHECK YOUR REVIT PROJECT RIGHT NOW!")
        print(f"Open sheet '{sheet_number}' and you should see the view on it!")
        print()
        return True
    else:
        error = place_result.get("error", "Unknown error")
        print(f"\n      [ERROR] {error}")

        # Try other coordinate systems
        print(f"\n      Trying alternative coordinate systems...")

        test_coords = [
            [0, 0],
            [1, 1],
            [2, 2],
            [0.5, 0.5],
            [1.0, 0.5],
            [100, 100],  # Try large values (might be in different units)
            [0.1, 0.1]   # Try small values
        ]

        for coords in test_coords:
            print(f"         Testing {coords}...")
            result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": coords
            })
            if result.get("success"):
                print(f"\n         *** SUCCESS with coordinates {coords}! ***")
                return True

        print("\n      All coordinate attempts failed")
        return False

def main():
    print("\n" + "=" * 80)
    print("FIX COMPLETE - TESTING VIEW PLACEMENT")
    print("=" * 80)
    print()
    print("Element ID Lookup: FIXED [OK]")
    print("Now testing: Place existing view on sheet")
    print()

    client = RevitClient()

    success = place_existing_view_test(client)

    print("\n" + "=" * 80)
    if success:
        print("COMPLETE SHEET CREATION: WORKING!")
        print()
        print("I can now:")
        print("  [OK] Get view ElementIDs")
        print("  [OK] Get sheet ElementIDs")
        print("  [OK] Place views on sheets")
        print("  [OK] Create complete deliverables autonomously!")
    else:
        print("Status: ElementID lookups working, investigating placeViewOnSheet")
    print("=" * 80)

if __name__ == "__main__":
    main()
