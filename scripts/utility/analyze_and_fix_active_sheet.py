"""
Analyze the currently active sheet and fix viewport scaling
Uses MCP methods to see what's happening and correct it
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("ANALYZING ACTIVE SHEET - LIVE CORRECTION")
    print("=" * 80)

    client = RevitClient()

    # Get the active view
    print("\n[STEP 1] Getting active view information...")
    active_result = client.send_request("getActiveView", {})

    if not active_result.get("success"):
        print(f"   ERROR: {active_result.get('error')}")
        return

    active_view_id = active_result.get("viewId")
    active_view_name = active_result.get("viewName")
    active_view_type = active_result.get("viewType")

    print(f"   Active View: {active_view_name}")
    print(f"   Type: {active_view_type}")
    print(f"   ID: {active_view_id}")

    # Check if it's a sheet
    if active_view_type != "DrawingSheet":
        print(f"\n   [ERROR] Active view is not a sheet!")
        print(f"   Please open the sheet DD24-A2.2 in Revit first")
        return

    sheet_id = active_view_id

    # Get all viewports on this sheet
    print("\n[STEP 2] Analyzing viewports on sheet...")
    viewports_result = client.send_request("getViewportBounds", {
        "sheetId": sheet_id
    })

    if not viewports_result.get("success"):
        print(f"   ERROR: {viewports_result.get('error')}")
        return

    viewports = viewports_result.get("viewports", [])
    print(f"   Found {len(viewports)} viewport(s) on sheet")

    if not viewports:
        print(f"   No viewports to analyze")
        return

    # Analyze each viewport
    for i, vp in enumerate(viewports, 1):
        vp_id = vp.get("viewportId")
        view_id = vp.get("viewId")
        view_name = vp.get("viewName")
        current_scale = vp.get("viewScale")
        vp_width = vp.get("width")
        vp_height = vp.get("height")
        center = vp.get("center")

        print(f"\n   Viewport {i}: {view_name}")
        print(f"      ID: {vp_id}")
        print(f"      Current scale: 1/{current_scale}\"")
        print(f"      Size: {vp_width:.2f}' x {vp_height:.2f}' ({vp_width*12:.1f}\" x {vp_height*12:.1f}\")")
        print(f"      Center: ({center[0]:.2f}, {center[1]:.2f})")

    # Analyze the sheet layout for issues
    print("\n[STEP 3] Checking for layout issues...")
    analyze_result = client.send_request("analyzeSheetLayout", {
        "sheetId": sheet_id
    })

    if not analyze_result.get("success"):
        print(f"   ERROR: {analyze_result.get('error')}")
        return

    sheet_width = analyze_result.get("sheetWidth", 0)
    sheet_height = analyze_result.get("sheetHeight", 0)
    issue_count = analyze_result.get("issueCount", 0)
    issues = analyze_result.get("issues", [])

    print(f"   Sheet size: {sheet_width:.2f}' x {sheet_height:.2f}' ({sheet_width*12:.1f}\" x {sheet_height*12:.1f}\")")
    print(f"   Issues found: {issue_count}")

    if issues:
        for issue in issues:
            print(f"\n   [ISSUE] {issue.get('type')}: {issue.get('message')}")
    else:
        print(f"   [OK] No overlaps or off-sheet issues detected")

    # Now let's assess if the viewport is too large
    print("\n[STEP 4] Assessing viewport size vs sheet size...")

    for vp in viewports:
        vp_width = vp.get("width")
        vp_height = vp.get("height")
        view_name = vp.get("viewName")
        view_id = vp.get("viewId")
        current_scale = vp.get("viewScale")

        # Estimate available drawing area on 24x36 sheet
        # Typical title block takes up about 6" on bottom, margins all around
        available_width = 2.5   # ~30" = 2.5 feet
        available_height = 2.0  # ~24" = 2.0 feet

        width_ratio = vp_width / available_width if available_width > 0 else 0
        height_ratio = vp_height / available_height if available_height > 0 else 0

        print(f"\n   {view_name}:")
        print(f"      Viewport: {vp_width*12:.1f}\" x {vp_height*12:.1f}\"")
        print(f"      Available: {available_width*12:.0f}\" x {available_height*12:.0f}\"")
        print(f"      Width usage: {width_ratio*100:.0f}%")
        print(f"      Height usage: {height_ratio*100:.0f}%")

        if width_ratio > 1.0 or height_ratio > 1.0:
            print(f"      [ISSUE] Viewport is TOO LARGE for sheet!")

            # Calculate new scale
            print(f"\n[STEP 5] Calculating corrected scale...")
            scale_result = client.send_request("calculateOptimalScale", {
                "viewId": view_id,
                "targetWidth": available_width,
                "targetHeight": available_height
            })

            if scale_result.get("success"):
                recommended_scale = scale_result.get("recommendedScale")
                scale_desc = scale_result.get("scaleDescription")

                print(f"      Current scale: 1/{current_scale}\"")
                print(f"      Recommended scale: {scale_desc}")

                if recommended_scale != current_scale:
                    print(f"\n[STEP 6] Applying corrected scale...")

                    set_scale_result = client.send_request("setViewScale", {
                        "viewId": view_id,
                        "scale": recommended_scale
                    })

                    if set_scale_result.get("success"):
                        print(f"      [SUCCESS] Scale adjusted to {scale_desc}!")

                        # Verify the fix
                        print(f"\n[STEP 7] Verifying the fix...")
                        verify_result = client.send_request("getViewportBounds", {
                            "sheetId": sheet_id
                        })

                        if verify_result.get("success"):
                            new_viewports = verify_result.get("viewports", [])
                            for new_vp in new_viewports:
                                if new_vp.get("viewId") == view_id:
                                    new_width = new_vp.get("width")
                                    new_height = new_vp.get("height")
                                    new_scale = new_vp.get("viewScale")

                                    print(f"      New size: {new_width:.2f}' x {new_height:.2f}' ({new_width*12:.1f}\" x {new_height*12:.1f}\")")
                                    print(f"      New scale: 1/{new_scale}\"")

                                    new_width_ratio = new_width / available_width
                                    new_height_ratio = new_height / available_height

                                    print(f"      Width usage: {new_width_ratio*100:.0f}%")
                                    print(f"      Height usage: {new_height_ratio*100:.0f}%")

                                    if new_width_ratio <= 1.0 and new_height_ratio <= 1.0:
                                        print(f"\n      [SUCCESS] View now fits on sheet!")
                                    else:
                                        print(f"\n      [WARN] View still too large, may need further adjustment")
                    else:
                        print(f"      [ERROR] Could not adjust scale: {set_scale_result.get('error')}")
            else:
                print(f"      [ERROR] Could not calculate scale: {scale_result.get('error')}")
        else:
            print(f"      [OK] Viewport fits within sheet boundaries")

    print("\n" + "=" * 80)
    print("ANALYSIS AND CORRECTION COMPLETE!")
    print("=" * 80)
    print(f"\nGO CHECK THE SHEET IN REVIT NOW!")
    print(f"The viewport should now be properly scaled to fit the 24x36 sheet")
    print("=" * 80)

if __name__ == "__main__":
    main()
