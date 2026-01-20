"""
COMPLETE DD PACKAGE - WORKING VERSION
Uses existing project views and places them on new sheets
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("CREATING COMPLETE DD PACKAGE - WITH VIEWS ON SHEETS!")
    print("=" * 80)

    client = RevitClient()

    successful_sheets = []
    failed_sheets = []

    # Get all existing views
    print("\n[STEP 1] Getting all existing views from project...")
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"   ERROR: {result.get('error')}")
        return

    views_data = result.get("result", {})
    all_views = views_data.get("views", [])

    # Categorize views by type
    floor_plans = [v for v in all_views if v.get("viewType") == "FloorPlan" and v.get("level") and not v.get("name", "").startswith("{")]
    elevations = [v for v in all_views if v.get("viewType") == "Elevation" and not v.get("name", "").startswith("{")]
    sections = [v for v in all_views if v.get("viewType") == "Section" and not v.get("name", "").startswith("{")]
    views_3d = [v for v in all_views if v.get("viewType") == "ThreeD" and not v.get("name", "").startswith("{")]

    print(f"   Found {len(floor_plans)} floor plans")
    print(f"   Found {len(elevations)} elevations")
    print(f"   Found {len(sections)} sections")
    print(f"   Found {len(views_3d)} 3D views")

    print("\n" + "=" * 80)
    print("[STEP 2] CREATING DD SHEETS WITH VIEWS PLACED")
    print("=" * 80)

    # Process Floor Plans
    if floor_plans:
        print("\n--- FLOOR PLAN SHEETS ---")
        for i, view in enumerate(floor_plans[:6], 1):  # First 6 floor plans
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"DD-A1.{i}"

            print(f"\n{i}. Creating sheet {sheet_num}")
            print(f"   View: {view_name} (ID: {view_id})")

            # Create sheet
            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - Design Development"
            })

            if not sheet_result.get("success"):
                error = sheet_result.get("error", "")
                print(f"   [FAILED] Sheet creation: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")
                continue

            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")

            # Place view on sheet
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.0]
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed on sheet! (Viewport ID: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] Placement: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Process Elevations
    if elevations:
        print("\n--- ELEVATION SHEETS ---")
        for i, view in enumerate(elevations[:4], 1):  # All elevations
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"DD-A2.{i}"

            print(f"\n{i}. Creating sheet {sheet_num}")
            print(f"   View: {view_name} (ID: {view_id})")

            # Create sheet
            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - Design Development"
            })

            if not sheet_result.get("success"):
                error = sheet_result.get("error", "")
                print(f"   [FAILED] Sheet creation: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")
                continue

            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")

            # Place view on sheet
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.0]
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed on sheet! (Viewport ID: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] Placement: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Process Sections (if any)
    if sections:
        print("\n--- SECTION SHEETS ---")
        for i, view in enumerate(sections[:4], 1):  # First 4 sections
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"DD-A3.{i}"

            print(f"\n{i}. Creating sheet {sheet_num}")
            print(f"   View: {view_name} (ID: {view_id})")

            # Create sheet
            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - Design Development"
            })

            if not sheet_result.get("success"):
                error = sheet_result.get("error", "")
                print(f"   [FAILED] Sheet creation: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")
                continue

            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")

            # Place view on sheet
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.0]
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed on sheet! (Viewport ID: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] Placement: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Process 3D Views
    if views_3d:
        print("\n--- 3D VIEW SHEETS ---")
        for i, view in enumerate(views_3d[:3], 1):  # First 3 3D views
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"DD-A5.{i}"

            print(f"\n{i}. Creating sheet {sheet_num}")
            print(f"   View: {view_name} (ID: {view_id})")

            # Create sheet
            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - Design Development"
            })

            if not sheet_result.get("success"):
                error = sheet_result.get("error", "")
                print(f"   [FAILED] Sheet creation: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")
                continue

            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")

            # Place view on sheet
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.0]
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed on sheet! (Viewport ID: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] Placement: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Create Cover Sheet
    if views_3d:
        print("\n--- COVER SHEET ---")
        view = views_3d[0]  # Use first 3D view for cover
        view_name = view.get("name")
        view_id = view.get("id")
        sheet_num = "DD-A0.1"

        print(f"\nCreating cover sheet {sheet_num}")
        print(f"   View: {view_name} (ID: {view_id})")

        sheet_result = client.send_request("createSheet", {
            "sheetNumber": sheet_num,
            "sheetName": "COVER SHEET - DESIGN DEVELOPMENT"
        })

        if sheet_result.get("success"):
            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] Sheet created (ID: {sheet_id})")

            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.5]  # Center position for cover
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed on sheet! (Viewport ID: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: COVER SHEET")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] Placement: {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Summary
    print("\n" + "=" * 80)
    print("DD PACKAGE CREATION COMPLETE!")
    print("=" * 80)

    total = len(successful_sheets) + len(failed_sheets)
    print(f"\nTotal Sheets: {total}")
    print(f"Successful (views placed): {len(successful_sheets)}")
    print(f"Failed: {len(failed_sheets)}")

    if successful_sheets:
        print("\n" + "=" * 80)
        print("SHEETS WITH VIEWS SUCCESSFULLY PLACED:")
        print("=" * 80)
        for sheet in successful_sheets:
            print(f"  [OK] {sheet}")

    if failed_sheets:
        print("\n" + "=" * 80)
        print("FAILED PLACEMENTS:")
        print("=" * 80)
        for sheet in failed_sheets:
            print(f"  [FAIL] {sheet}")

    print("\n" + "=" * 80)
    print("GO CHECK YOUR REVIT PROJECT NOW!")
    print("Open the DD-A1.x, DD-A2.x sheets to see views on them!")
    print("=" * 80)

if __name__ == "__main__":
    main()
