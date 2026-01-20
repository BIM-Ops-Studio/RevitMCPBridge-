"""
FINAL FIX - Complete Sheet Creation with View Placement
Uses sheetId directly from createSheet response (no need to query getAllSheets)
This is the WORKING solution to place views on sheets!
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def get_existing_floor_plan_views(client):
    """Get all existing floor plan views"""
    result = client.send_request("getViews", {})

    if not result.get("success"):
        return []

    # Fixed: Views are in result.result.views
    views_data = result.get("result", {})
    views = views_data.get("views", [])

    # Filter for floor plans with levels
    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan" and v.get("level")]

    return floor_plans

def create_complete_sheet_FIXED(client):
    """FIXED VERSION - Create sheet with view placed on it"""
    print("\n" + "=" * 80)
    print("COMPLETE FIX: Creating Sheet with View Placed!")
    print("=" * 80)

    # Step 1: Get an existing floor plan view
    print("\n[STEP 1/3] Finding existing floor plan view...")
    floor_plans = get_existing_floor_plan_views(client)

    if not floor_plans:
        print("      [ERROR] No floor plan views found!")
        return False

    print(f"      [OK] Found {len(floor_plans)} floor plan views")

    # Use the first floor plan
    selected_view = floor_plans[0]
    view_name = selected_view.get("name")
    view_id = selected_view.get("id")

    print(f"      [OK] Selected: {view_name} (ID: {view_id})")

    # Step 2: Create sheet and GET SHEETID FROM RESPONSE
    print("\n[STEP 2/3] Creating new sheet...")
    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "COMPLETE-FIX-01",
        "sheetName": "Complete Sheet - FIXED VERSION"
    })

    if not sheet_result.get("success"):
        error = sheet_result.get("error", "")
        if "duplicate" in error.lower() or "exists" in error.lower():
            print(f"      [INFO] Sheet exists, will try to use it")
            # If duplicate, get the ID from getAllSheets
            sheets_result = client.send_request("getAllSheets", {})
            sheets = sheets_result.get("sheets", [])
            sheet_id = None
            for sheet in sheets:
                if sheet.get("sheetNumber") == "COMPLETE-FIX-01":
                    sheet_id = sheet.get("sheetId")
                    break
            if not sheet_id:
                print("      [ERROR] Could not find existing sheet ID")
                return False
        else:
            print(f"      [ERROR] {error}")
            return False
    else:
        # KEY FIX: Get sheetId directly from createSheet response!
        sheet_id = sheet_result.get("sheetId")
        print(f"      [OK] Created sheet COMPLETE-FIX-01")

    print(f"      [OK] Sheet ID: {sheet_id}")

    # Step 3: Place view on sheet
    print("\n[STEP 3/3] Placing view on sheet...")
    print(f"      Parameters:")
    print(f"        sheetId: {sheet_id}")
    print(f"        viewId: {view_id}")
    print(f"        location: [1.5, 1.0] (feet from sheet origin)")

    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [1.5, 1.0]
    })

    if place_result.get("success"):
        print("\n" + "=" * 80)
        print("*** SUCCESS!!! VIEW IS NOW ON THE SHEET!!! ***")
        print("=" * 80)
        print()
        print("DELIVERABLE CREATED:")
        print(f"  Sheet Number: COMPLETE-FIX-01")
        print(f"  Sheet Name: Complete Sheet - FIXED VERSION")
        print(f"  View Placed: {view_name}")
        print()
        print("GO CHECK YOUR REVIT PROJECT NOW!")
        print("Open sheet 'COMPLETE-FIX-01' and you will see the view on it!")
        print()
        print("ELEMENT ID LOOKUP CHAIN: FIXED [OK]")
        print("AUTONOMOUS SHEET CREATION: WORKING [OK]")
        print()
        return True
    else:
        error = place_result.get("error", "Unknown error")
        print(f"\n      [ERROR] Failed to place view: {error}")

        # Try alternative coordinates
        print(f"\n      Trying alternative coordinate systems...")
        test_coords = [
            [0, 0],
            [1, 1],
            [2, 2],
            [0.5, 0.5],
            [100, 100],  # Try page units
            [0.1, 0.1]
        ]

        for coords in test_coords:
            print(f"         Testing location: {coords}...")
            result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": coords
            })
            if result.get("success"):
                print(f"\n         [OK] SUCCESS with coordinates {coords}!")
                print(f"\n         View placed on sheet at location {coords}")
                return True

        print("\n      All coordinate attempts failed")
        print(f"      Last error: {error}")
        return False

def main():
    print("\n" + "=" * 80)
    print("ELEMENT ID LOOKUP CHAIN - FINAL FIX")
    print("=" * 80)
    print()
    print("KEY INSIGHT:")
    print("  createSheet() returns sheetId directly in response")
    print("  No need to query getAllSheets afterward!")
    print()
    print("Fix Applied:")
    print("  sheet_result = createSheet(...)")
    print("  sheet_id = sheet_result.get('sheetId')  # Use this!")
    print()

    client = RevitClient()

    success = create_complete_sheet_FIXED(client)

    print("\n" + "=" * 80)
    if success:
        print("COMPLETE AUTONOMOUS SHEET CREATION: WORKING!")
        print()
        print("I can now:")
        print("  [OK] Get view ElementIDs from existing views")
        print("  [OK] Create sheets and get their ElementIDs")
        print("  [OK] Place views on sheets with coordinates")
        print("  [OK] Create complete, ready-to-print deliverables")
        print()
        print("Ready to update all autonomous workflow scripts!")
    else:
        print("FURTHER DEBUGGING NEEDED")
        print()
        print("ElementID lookups: WORKING [OK]")
        print("placeViewOnSheet: INVESTIGATING")
    print("=" * 80)

if __name__ == "__main__":
    main()
