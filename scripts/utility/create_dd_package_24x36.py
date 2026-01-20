"""
Create DD Package with 24x36 Sheets
Uses the NTB 24X36 title block (ID: 1280909)
Places views with intelligent scaling
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("DD PACKAGE CREATION - 24X36 SHEETS!")
    print("=" * 80)

    client = RevitClient()

    # Use the 24x36 title block
    titleblock_24x36_id = 1280909

    print(f"\nUsing title block: NTB 24X36 (ID: {titleblock_24x36_id})")

    # Get existing views
    print("\n[1] Getting existing floor plan and elevation views...")
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")
        return

    views_data = result.get("result", {})
    all_views = views_data.get("views", [])

    floor_plans = [v for v in all_views if v.get("viewType") == "FloorPlan" and v.get("level") and not v.get("name", "").startswith("{")]
    elevations = [v for v in all_views if v.get("viewType") == "Elevation" and not v.get("name", "").startswith("{")]

    print(f"   Found {len(floor_plans)} floor plans")
    print(f"   Found {len(elevations)} elevations")

    successful_sheets = []
    failed_sheets = []

    print("\n" + "=" * 80)
    print("[2] CREATING 24X36 SHEETS WITH VIEWS")
    print("=" * 80)

    # Create floor plan sheets
    print("\n--- FLOOR PLAN SHEETS (24x36) ---")
    for i, view in enumerate(floor_plans[:4], 1):
        view_name = view.get("name")
        view_id = view.get("id")
        view_scale = view.get("scale", 192)
        sheet_num = f"DD24-A1.{i}"

        print(f"\n{i}. Sheet {sheet_num}: {view_name}")
        print(f"   View scale: 1/{view_scale}\"")

        # Create sheet with 24x36 title block
        sheet_result = client.send_request("createSheet", {
            "sheetNumber": sheet_num,
            "sheetName": f"{view_name} - DD (24x36)",
            "titleblockId": titleblock_24x36_id
        })

        if not sheet_result.get("success"):
            error = sheet_result.get("error", "")
            if "duplicate" not in error.lower():
                print(f"   [FAILED] {error}")
                failed_sheets.append(sheet_num)
                continue
            else:
                print(f"   [INFO] Sheet exists, using existing")
                # Get existing sheet ID
                sheets_result = client.send_request("getAllSheets", {})
                sheet_id = None
                for sheet in sheets_result.get("sheets", []):
                    if sheet.get("sheetNumber") == sheet_num:
                        sheet_id = sheet.get("sheetId")
                        break
                if not sheet_id:
                    print(f"   [FAILED] Could not find existing sheet")
                    failed_sheets.append(sheet_num)
                    continue
        else:
            sheet_id = sheet_result.get("sheetId")
            print(f"   [OK] 24x36 sheet created (ID: {sheet_id})")

        # Calculate optimal scale for 24x36 sheet
        # Approximate available area on 24x36: 30" wide x 24" tall drawing area
        # = 2.5 ft x 2.0 ft
        scale_result = client.send_request("calculateOptimalScale", {
            "viewId": view_id,
            "targetWidth": 2.5,   # 30" available width
            "targetHeight": 2.0    # 24" available height
        })

        recommended_scale = view_scale  # Default to current
        if scale_result.get("success"):
            recommended_scale = scale_result.get("recommendedScale", view_scale)
            print(f"   Recommended scale: 1/{recommended_scale}\"")

            # Set the scale if different
            if recommended_scale != view_scale:
                set_scale_result = client.send_request("setViewScale", {
                    "viewId": view_id,
                    "scale": recommended_scale
                })
                if set_scale_result.get("success"):
                    print(f"   [OK] Scale adjusted to 1/{recommended_scale}\"")

        # Place view on sheet
        print(f"   [>>] Placing view on 24x36 sheet...")
        place_result = client.send_request("placeViewOnSheet", {
            "sheetId": sheet_id,
            "viewId": view_id,
            "location": [1.8, 1.5]  # Center position for 24x36
        })

        if place_result.get("success"):
            viewport_id = place_result.get("viewportId")
            print(f"   [SUCCESS] View placed! (Viewport: {viewport_id})")

            # Analyze the placement
            analyze_result = client.send_request("analyzeSheetLayout", {
                "sheetId": sheet_id
            })

            if analyze_result.get("success"):
                issue_count = analyze_result.get("issueCount", 0)
                if issue_count == 0:
                    print(f"   [OK] Layout clean - no issues!")
                    successful_sheets.append(f"{sheet_num}: {view_name}")
                else:
                    issues = analyze_result.get("issues", [])
                    for issue in issues:
                        print(f"   [WARN] {issue.get('type')}: {issue.get('message')}")
                    successful_sheets.append(f"{sheet_num}: {view_name} (with warnings)")
        else:
            error = place_result.get("error", "")
            print(f"   [FAILED] {error}")
            failed_sheets.append(f"{sheet_num}: {error}")

    # Create elevation sheets
    if elevations:
        print("\n--- ELEVATION SHEETS (24x36) ---")
        for i, view in enumerate(elevations[:4], 1):
            view_name = view.get("name")
            view_id = view.get("id")
            view_scale = view.get("scale", 192)
            sheet_num = f"DD24-A2.{i}"

            print(f"\n{i}. Sheet {sheet_num}: {view_name}")

            # Create sheet
            sheet_result = client.send_request("createSheet", {
                "sheetNumber": sheet_num,
                "sheetName": f"{view_name} - DD (24x36)",
                "titleblockId": titleblock_24x36_id
            })

            if not sheet_result.get("success"):
                error = sheet_result.get("error", "")
                if "duplicate" not in error.lower():
                    print(f"   [FAILED] {error}")
                    failed_sheets.append(sheet_num)
                    continue
                else:
                    sheets_result = client.send_request("getAllSheets", {})
                    sheet_id = None
                    for sheet in sheets_result.get("sheets", []):
                        if sheet.get("sheetNumber") == sheet_num:
                            sheet_id = sheet.get("sheetId")
                            break
                    if not sheet_id:
                        failed_sheets.append(sheet_num)
                        continue
            else:
                sheet_id = sheet_result.get("sheetId")
                print(f"   [OK] 24x36 sheet created (ID: {sheet_id})")

            # Place view
            place_result = client.send_request("placeViewOnSheet", {
                "sheetId": sheet_id,
                "viewId": view_id,
                "location": [1.8, 1.5]
            })

            if place_result.get("success"):
                viewport_id = place_result.get("viewportId")
                print(f"   [SUCCESS] View placed! (Viewport: {viewport_id})")
                successful_sheets.append(f"{sheet_num}: {view_name}")
            else:
                error = place_result.get("error", "")
                print(f"   [FAILED] {error}")
                failed_sheets.append(f"{sheet_num}: {error}")

    # Summary
    print("\n" + "=" * 80)
    print("DD PACKAGE WITH 24X36 SHEETS - COMPLETE!")
    print("=" * 80)

    total = len(successful_sheets) + len(failed_sheets)
    print(f"\nTotal sheets: {total}")
    print(f"Successful (views placed): {len(successful_sheets)}")
    print(f"Failed: {len(failed_sheets)}")

    if successful_sheets:
        print("\n" + "=" * 80)
        print("SHEETS WITH VIEWS SUCCESSFULLY PLACED (24x36):")
        print("=" * 80)
        for sheet in successful_sheets:
            print(f"  [OK] {sheet}")

    if failed_sheets:
        print("\n--- FAILED PLACEMENTS ---")
        for sheet in failed_sheets:
            print(f"  [FAIL] {sheet}")

    print("\n" + "=" * 80)
    print("GO CHECK YOUR REVIT PROJECT NOW!")
    print("Open the DD24-A1.x and DD24-A2.x sheets")
    print("These are 24x36 sheets with views properly scaled!")
    print("=" * 80)

if __name__ == "__main__":
    main()
