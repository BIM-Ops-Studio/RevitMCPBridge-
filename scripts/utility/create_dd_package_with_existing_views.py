"""
DD Package using EXISTING views from the project
Find available views and place them on sheets
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("DD PACKAGE - USING EXISTING PROJECT VIEWS")
    print("=" * 80)

    client = RevitClient()

    # Get all existing views
    print("\n[1] Getting all existing views from project...")
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")
        return

    views_data = result.get("result", {})
    views = views_data.get("views", [])

    # Categorize views
    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan" and v.get("level") and not v.get("isTemplate")]
    elevations = [v for v in views if v.get("viewType") == "Elevation"]
    sections = [v for v in views if v.get("viewType") == "Section"]
    views_3d = [v for v in views if v.get("viewType") == "ThreeD"]

    print(f"   Found {len(floor_plans)} floor plans")
    print(f"   Found {len(elevations)} elevations")
    print(f"   Found {len(sections)} sections")
    print(f"   Found {len(views_3d)} 3D views")

    successful = []
    failed = []

    print("\n" + "=" * 80)
    print("[2] CREATING SHEETS WITH VIEWS")
    print("=" * 80)

    # Floor Plans
    print("\n--- FLOOR PLANS ---")
    for i, view in enumerate(floor_plans[:4], 1):  # First 4 floor plans
        view_name = view.get("name")
        view_id = view.get("id")
        sheet_num = f"A1.{i}"

        print(f"\n   Sheet {sheet_num}: {view_name}")

        # Create sheet
        sheet_result = client.send_request("createSheet", {
            "sheetNumber": sheet_num,
            "sheetName": f"{view_name} - DD"
        })

        sheet_id = None
        if sheet_result.get("success"):
            sheet_id = sheet_result.get("sheetId")
            print(f"      [OK] Sheet created (ID: {sheet_id})")
        else:
            error = sheet_result.get("error", "")
            if "duplicate" in error.lower():
                sheets_result = client.send_request("getAllSheets", {})
                if sheets_result.get("success"):
                    for sheet in sheets_result.get("sheets", []):
                        if sheet.get("sheetNumber") == sheet_num:
                            sheet_id = sheet.get("sheetId")
                            print(f"      [INFO] Using existing sheet (ID: {sheet_id})")
                            break

        if sheet_id:
            print(f"      [>>] Placing view (ID: {view_id})...")
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.5, 1.0]
            })

            if place_result.get("success"):
                print(f"      [SUCCESS] View placed on sheet!")
                successful.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"      [FAILED] {error}")
                failed.append(f"{sheet_num}: {error}")

    # Elevations
    if elevations:
        print("\n--- ELEVATIONS ---")
        for i, view in enumerate(elevations[:4], 1):  # All elevations
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"A2.{i}"

            print(f"\n   Sheet {sheet_num}: {view_name}")

            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - DD"
            })

            sheet_id = None
            if sheet_result.get("success"):
                sheet_id = sheet_result.get("sheetId")
                print(f"      [OK] Sheet created (ID: {sheet_id})")
            else:
                error = sheet_result.get("error", "")
                if "duplicate" in error.lower():
                    sheets_result = client.send_request("getAllSheets", {})
                    if sheets_result.get("success"):
                        for sheet in sheets_result.get("sheets", []):
                            if sheet.get("sheetNumber") == sheet_num:
                                sheet_id = sheet.get("sheetId")
                                print(f"      [INFO] Using existing sheet (ID: {sheet_id})")
                                break

            if sheet_id:
                print(f"      [>>] Placing view (ID: {view_id})...")
                place_result = client.send_request("placeViewOnSheet", {
                    "sheetId": sheet_id,
                    "viewId": view_id,
                    "location": [1.5, 1.0]
                })

                if place_result.get("success"):
                    print(f"      [SUCCESS] View placed on sheet!")
                    successful.append(f"{sheet_num}: {view_name}")
                else:
                    error = place_result.get("error", "")
                    print(f"      [FAILED] {error}")
                    failed.append(f"{sheet_num}: {error}")

    # Sections (if any)
    if sections:
        print("\n--- SECTIONS ---")
        for i, view in enumerate(sections[:3], 1):  # First 3 sections
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"A3.{i}"

            print(f"\n   Sheet {sheet_num}: {view_name}")

            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - DD"
            })

            sheet_id = None
            if sheet_result.get("success"):
                sheet_id = sheet_result.get("sheetId")
                print(f"      [OK] Sheet created (ID: {sheet_id})")
            else:
                error = sheet_result.get("error", "")
                if "duplicate" in error.lower():
                    sheets_result = client.send_request("getAllSheets", {})
                    if sheets_result.get("success"):
                        for sheet in sheets_result.get("sheets", []):
                            if sheet.get("sheetNumber") == sheet_num:
                                sheet_id = sheet.get("sheetId")
                                print(f"      [INFO] Using existing sheet (ID: {sheet_id})")
                                break

            if sheet_id:
                print(f"      [>>] Placing view (ID: {view_id})...")
                place_result = client.send_request("placeViewOnSheet", {
                    "sheetId": sheet_id,
                    "viewId": view_id,
                    "location": [1.5, 1.0]
                })

                if place_result.get("success"):
                    print(f"      [SUCCESS] View placed on sheet!")
                    successful.append(f"{sheet_num}: {view_name}")
                else:
                    error = place_result.get("error", "")
                    print(f"      [FAILED] {error}")
                    failed.append(f"{sheet_num}: {error}")

    # 3D Views
    if views_3d:
        print("\n--- 3D VIEWS ---")
        for i, view in enumerate(views_3d[:2], 1):  # First 2 3D views
            view_name = view.get("name")
            view_id = view.get("id")
            sheet_num = f"A5.{i}"

            print(f"\n   Sheet {sheet_num}: {view_name}")

            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - DD"
            })

            sheet_id = None
            if sheet_result.get("success"):
                sheet_id = sheet_result.get("sheetId")
                print(f"      [OK] Sheet created (ID: {sheet_id})")
            else:
                error = sheet_result.get("error", "")
                if "duplicate" in error.lower():
                    sheets_result = client.send_request("getAllSheets", {})
                    if sheets_result.get("success"):
                        for sheet in sheets_result.get("sheets", []):
                            if sheet.get("sheetNumber") == sheet_num:
                                sheet_id = sheet.get("sheetId")
                                print(f"      [INFO] Using existing sheet (ID: {sheet_id})")
                                break

            if sheet_id:
                print(f"      [>>] Placing view (ID: {view_id})...")
                place_result = client.send_request("placeViewOnSheet", {
                    "sheetId": sheet_id,
                    "viewId": view_id,
                    "location": [1.5, 1.0]
                })

                if place_result.get("success"):
                    print(f"      [SUCCESS] View placed on sheet!")
                    successful.append(f"{sheet_num}: {view_name}")
                else:
                    error = place_result.get("error", "")
                    print(f"      [FAILED] {error}")
                    failed.append(f"{sheet_num}: {error}")

    # Summary
    print("\n" + "=" * 80)
    print("DD PACKAGE COMPLETE!")
    print("=" * 80)
    print(f"\nSuccessful placements: {len(successful)}")
    print(f"Failed placements: {len(failed)}")

    if successful:
        print("\n--- SHEETS WITH VIEWS PLACED ---")
        for item in successful:
            print(f"  [OK] {item}")

    if failed:
        print("\n--- PLACEMENT FAILURES ---")
        for item in failed:
            print(f"  [FAIL] {item}")

    print("\n" + "=" * 80)
    if successful:
        print("GO CHECK YOUR REVIT PROJECT!")
        print("Open the A1.x, A2.x sheets to see views on them!")
    print("=" * 80)

if __name__ == "__main__":
    main()
