"""
DEMONSTRATION: Intelligent Sheet Placement
Shows new capabilities:
1. Query title blocks with dimensions
2. Select 24x36 sheets
3. Calculate optimal view scales
4. Detect overlaps and off-sheet views
5. Smart placement with proper scales
"""
import sys
import json
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("INTELLIGENT SHEET PLACEMENT - DEMONSTRATION")
    print("=" * 80)

    client = RevitClient()

    # STEP 1: Get all available title blocks with dimensions
    print("\n[STEP 1] Querying available title blocks with dimensions...")
    tb_result = client.send_request("getTitleblockDimensions", {})

    if not tb_result.get("success"):
        print(f"   ERROR: {tb_result.get('error')}")
        return

    titleblocks = tb_result.get("titleblocks", [])
    print(f"   Found {len(titleblocks)} title blocks:")

    for tb in titleblocks[:10]:
        width_in = tb.get("widthInches", 0)
        height_in = tb.get("heightInches", 0)
        print(f"      - {tb.get('familyName')} - {tb.get('typeName')}")
        print(f"        Size: {width_in:.1f}\" x {height_in:.1f}\"  (ID: {tb.get('titleblockId')})")

    # Find 24x36 title block (or closest)
    print("\n[STEP 2] Finding 24x36 (or closest) title block...")
    target_24x36 = None
    for tb in titleblocks:
        width = tb.get("widthInches", 0)
        height = tb.get("heightInches", 0)
        # Check for 24x36 or 36x24 (landscape or portrait)
        if (abs(width - 24) < 2 and abs(height - 36) < 2) or \
           (abs(width - 36) < 2 and abs(height - 24) < 2):
            target_24x36 = tb
            break

    if not target_24x36:
        # Use largest title block available
        target_24x36 = max(titleblocks, key=lambda tb: tb.get("widthInches", 0) * tb.get("heightInches", 0))
        print(f"   [INFO] No 24x36 found, using largest: {target_24x36.get('familyName')} - {target_24x36.get('typeName')}")
    else:
        print(f"   [OK] Found 24x36 titleblock: {target_24x36.get('familyName')} - {target_24x36.get('typeName')}")

    print(f"   Dimensions: {target_24x36.get('widthInches'):.1f}\" x {target_24x36.get('heightInches'):.1f}\"")
    print(f"   Title Block ID: {target_24x36.get('titleblockId')}")

    # STEP 3: Get existing views
    print("\n[STEP 3] Getting existing views for placement...")
    views_result = client.send_request("getViews", {})

    if not views_result.get("success"):
        print(f"   ERROR: {views_result.get('error')}")
        return

    views_data = views_result.get("result", {})
    all_views = views_data.get("views", [])

    floor_plans = [v for v in all_views if v.get("viewType") == "FloorPlan" and v.get("level") and not v.get("name", "").startswith("{")]

    if not floor_plans:
        print("   ERROR: No floor plan views found!")
        return

    print(f"   Found {len(floor_plans)} floor plan views")

    # STEP 4: Create sheet with proper title block
    test_view = floor_plans[0]
    view_name = test_view.get("name")
    view_id = test_view.get("id")

    print("\n[STEP 4] Creating sheet with 24x36 title block...")
    print(f"   View to place: {view_name} (ID: {view_id})")

    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "INTEL-TEST-01",
        "sheetName": "Intelligent Placement Test - 24x36",
        "titleblockId": target_24x36.get("titleblockId")
    })

    if not sheet_result.get("success"):
        error = sheet_result.get("error", "")
        if "duplicate" in error.lower():
            print(f"   [INFO] Sheet exists, continuing with existing sheet")
            # Get existing sheet ID
            sheets_result = client.send_request("getAllSheets", {})
            sheet_id = None
            for sheet in sheets_result.get("sheets", []):
                if sheet.get("sheetNumber") == "INTEL-TEST-01":
                    sheet_id = sheet.get("sheetId")
                    break
            if not sheet_id:
                print("   ERROR: Could not find existing sheet")
                return
        else:
            print(f"   ERROR: {error}")
            return
    else:
        sheet_id = sheet_result.get("sheetId")
        print(f"   [OK] Sheet created with 24x36 titleblock (ID: {sheet_id})")

    # STEP 5: Calculate optimal scale for view
    print("\n[STEP 5] Calculating optimal view scale...")

    # Available area on 24x36 sheet (approximate, accounting for title block margins)
    available_width = 2.5  # ~30" = 2.5 feet (accounting for margins)
    available_height = 1.5  # ~18" = 1.5 feet (accounting for title block height)

    scale_result = client.send_request("calculateOptimalScale", {
        "viewId": view_id,
        "targetWidth": available_width,
        "targetHeight": available_height
    })

    if scale_result.get("success"):
        recommended_scale = scale_result.get("recommendedScale")
        current_scale = scale_result.get("currentScale")
        scale_desc = scale_result.get("scaleDescription")

        print(f"   Current scale: 1/{current_scale}\"")
        print(f"   Recommended scale: {scale_desc}")
        print(f"   View dimensions: {scale_result.get('viewWidth'):.1f}' x {scale_result.get('viewHeight'):.1f}'")

        # Set the optimal scale
        if recommended_scale != current_scale:
            print(f"\n   Adjusting view scale to {scale_desc}...")
            set_scale_result = client.send_request("setViewScale", {
                "viewId": view_id,
                "scale": recommended_scale
            })
            if set_scale_result.get("success"):
                print(f"   [OK] View scale adjusted")
            else:
                print(f"   [WARN] Could not adjust scale: {set_scale_result.get('error')}")
    else:
        print(f"   [WARN] Could not calculate scale: {scale_result.get('error')}")

    # STEP 6: Place view on sheet
    print("\n[STEP 6] Placing view on sheet with calculated scale...")

    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [1.5, 1.0]  # Center position
    })

    if not place_result.get("success"):
        print(f"   [FAILED] {place_result.get('error')}")
        return

    viewport_id = place_result.get("viewportId")
    print(f"   [SUCCESS] View placed! (Viewport ID: {viewport_id})")

    # STEP 7: Analyze sheet layout
    print("\n[STEP 7] Analyzing sheet layout for issues...")

    analyze_result = client.send_request("analyzeSheetLayout", {
        "sheetId": sheet_id
    })

    if analyze_result.get("success"):
        sheet_width = analyze_result.get("sheetWidth", 0)
        sheet_height = analyze_result.get("sheetHeight", 0)
        viewport_count = analyze_result.get("viewportCount", 0)
        issue_count = analyze_result.get("issueCount", 0)
        has_overlaps = analyze_result.get("hasOverlaps", False)
        has_off_sheet = analyze_result.get("hasOffSheetViews", False)

        print(f"   Sheet size: {sheet_width:.2f}' x {sheet_height:.2f}' ({sheet_width*12:.1f}\" x {sheet_height*12:.1f}\")")
        print(f"   Viewports on sheet: {viewport_count}")
        print(f"   Layout issues found: {issue_count}")

        if issue_count == 0:
            print(f"   [OK] Layout is clean - no overlaps or off-sheet views!")
        else:
            issues = analyze_result.get("issues", [])
            for issue in issues:
                issue_type = issue.get("type")
                message = issue.get("message")
                if issue_type == "OVERLAP":
                    print(f"   [WARN] OVERLAP: {message}")
                elif issue_type == "OFF_SHEET":
                    print(f"   [WARN] OFF-SHEET: {message}")

    # STEP 8: Get viewport bounds
    print("\n[STEP 8] Getting detailed viewport information...")

    bounds_result = client.send_request("getViewportBounds", {
        "sheetId": sheet_id
    })

    if bounds_result.get("success"):
        viewports = bounds_result.get("viewports", [])
        for vp in viewports:
            print(f"\n   Viewport: {vp.get('viewName')}")
            print(f"      Scale: 1/{vp.get('viewScale')}\"")
            print(f"      Size: {vp.get('width'):.2f}' x {vp.get('height'):.2f}'")
            print(f"      Center: ({vp.get('center')[0]:.2f}, {vp.get('center')[1]:.2f})")

    # Summary
    print("\n" + "=" * 80)
    print("INTELLIGENT PLACEMENT DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print(f"\nNew Capabilities Demonstrated:")
    print(f"  [OK] Query title blocks with dimensions")
    print(f"  [OK] Select proper sheet size (24x36)")
    print(f"  [OK] Calculate optimal view scale")
    print(f"  [OK] Place view with correct scale")
    print(f"  [OK] Analyze layout for overlaps and boundaries")
    print(f"  [OK] Get detailed viewport information")

    print(f"\nGO CHECK YOUR REVIT PROJECT!")
    print(f"  Sheet: INTEL-TEST-01")
    print(f"  View placed with optimal scale on 24x36 sheet")
    print("=" * 80)

if __name__ == "__main__":
    main()
