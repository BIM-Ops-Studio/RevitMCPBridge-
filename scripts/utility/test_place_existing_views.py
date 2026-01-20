"""
Test placing EXISTING views on sheets
Find what views actually exist in the project and place them
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("TESTING: Placing EXISTING Views on New Sheets")
    print("=" * 80)

    client = RevitClient()

    # Step 1: Get ALL existing views
    print("\n[STEP 1] Getting all existing views from project...")
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")
        return

    views_data = result.get("result", {})
    views = views_data.get("views", [])

    print(f"   Found {len(views)} total views")

    # Categorize views by type
    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan" and v.get("level")]
    elevations = [v for v in views if v.get("viewType") == "Elevation"]
    sections = [v for v in views if v.get("viewType") == "Section"]
    schedules = [v for v in views if v.get("viewType") == "Schedule"]
    views_3d = [v for v in views if v.get("viewType") == "ThreeD"]

    print(f"\n   Floor Plans: {len(floor_plans)}")
    print(f"   Elevations: {len(elevations)}")
    print(f"   Sections: {len(sections)}")
    print(f"   Schedules: {len(schedules)}")
    print(f"   3D Views: {len(views_3d)}")

    # Step 2: Try to place one of each type on a sheet
    print("\n" + "=" * 80)
    print("[STEP 2] Testing View Placement (One of Each Type)")
    print("=" * 80)

    tests = []

    if floor_plans:
        tests.append({
            "view": floor_plans[0],
            "sheet_num": "TEST-FP-01",
            "sheet_name": "Test Floor Plan",
            "location": [1.5, 1.0]
        })

    if elevations:
        tests.append({
            "view": elevations[0],
            "sheet_num": "TEST-EL-01",
            "sheet_name": "Test Elevation",
            "location": [1.5, 1.0]
        })

    if sections:
        tests.append({
            "view": sections[0],
            "sheet_num": "TEST-SEC-01",
            "sheet_name": "Test Section",
            "location": [1.5, 1.0]
        })

    if schedules:
        tests.append({
            "view": schedules[0],
            "sheet_num": "TEST-SCH-01",
            "sheet_name": "Test Schedule",
            "location": [0.5, 0.5]  # Different location for schedules
        })

    if views_3d:
        tests.append({
            "view": views_3d[0],
            "sheet_num": "TEST-3D-01",
            "sheet_name": "Test 3D View",
            "location": [1.5, 1.0]
        })

    successful_placements = []
    failed_placements = []

    for test in tests:
        view = test["view"]
        view_name = view.get("name")
        view_id = view.get("id")
        view_type = view.get("viewType")

        print(f"\n--- Testing {view_type}: {view_name} (ID: {view_id}) ---")

        # Create sheet
        print(f"   Creating sheet {test['sheet_num']}...")
        sheet_result = client.send_request("createSheet", {
            "sheetNumber": test["sheet_num"],
            "sheetName": test["sheet_name"]
        })

        sheet_id = None
        if sheet_result.get("success"):
            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")
        else:
            error = sheet_result.get("error", "")
            if "duplicate" in error.lower():
                # Get existing sheet
                sheets_result = client.send_request("getAllSheets", {})
                if sheets_result.get("success"):
                    for sheet in sheets_result.get("sheets", []):
                        if sheet.get("sheetNumber") == test["sheet_num"]:
                            sheet_id = sheet.get("sheetId")
                            print(f"   [OK] Using existing sheet (ID: {sheet_id})")
                            break

        if not sheet_id:
            print(f"   [ERROR] Could not get sheet ID")
            failed_placements.append(f"{view_type}: No sheet ID")
            continue

        # Place view on sheet
        print(f"   Placing view on sheet...")
        print(f"      sheetId: {sheet_id}")
        print(f"      viewId: {view_id}")
        print(f"      location: {test['location']}")

        place_result = client.send_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": view_id,
            "location": test["location"]
        })

        if place_result.get("success"):
            print(f"   [SUCCESS] {view_type} placed on sheet!")
            successful_placements.append(f"{test['sheet_num']}: {view_name}")
        else:
            error = place_result.get("error", "Unknown")
            print(f"   [FAILED] {error}")
            failed_placements.append(f"{view_type}: {error}")

    # Summary
    print("\n" + "=" * 80)
    print("PLACEMENT TEST RESULTS")
    print("=" * 80)
    print(f"\nSuccessful: {len(successful_placements)}/{len(tests)}")
    print(f"Failed: {len(failed_placements)}/{len(tests)}")

    if successful_placements:
        print("\n--- SUCCESSFUL PLACEMENTS ---")
        for item in successful_placements:
            print(f"  [OK] {item}")

    if failed_placements:
        print("\n--- FAILED PLACEMENTS ---")
        for item in failed_placements:
            print(f"  [FAIL] {item}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
