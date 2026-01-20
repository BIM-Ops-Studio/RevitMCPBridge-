"""
PROPER Sheet Layout Analysis and Correction
Now with REAL sheet boundary detection and smart positioning
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("PROPER SHEET LAYOUT - WITH REAL BOUNDARY DETECTION")
    print("=" * 80)

    client = RevitClient()

    # Get active sheet
    print("\n[STEP 1] Getting active sheet...")
    active_result = client.send_request("getActiveView", {})

    if not active_result.get("success"):
        print(f"ERROR: {active_result.get('error')}")
        return

    if active_result.get("viewType") != "DrawingSheet":
        print("ERROR: Please open a sheet first (like DD24-A2.2)")
        return

    sheet_id = active_result.get("viewId")
    sheet_name = active_result.get("viewName")

    print(f"   Sheet: {sheet_name}")
    print(f"   ID: {sheet_id}")

    # Analyze the sheet with NEW boundary detection
    print("\n[STEP 2] Analyzing sheet boundaries (FIXED METHOD)...")
    analyze_result = client.send_request("analyzeSheetLayout", {
        "sheetId": sheet_id
    })

    if not analyze_result.get("success"):
        print(f"ERROR: {analyze_result.get('error')}")
        return

    # Get REAL sheet dimensions
    sheet_width_ft = analyze_result.get("sheetWidth", 0)
    sheet_height_ft = analyze_result.get("sheetHeight", 0)
    sheet_width_in = analyze_result.get("sheetWidthInches", 0)
    sheet_height_in = analyze_result.get("sheetHeightInches", 0)

    drawing_width_ft = analyze_result.get("drawingAreaWidth", 0)
    drawing_height_ft = analyze_result.get("drawingAreaHeight", 0)
    drawing_width_in = analyze_result.get("drawingAreaWidthInches", 0)
    drawing_height_in = analyze_result.get("drawingAreaHeightInches", 0)

    title_block_height = analyze_result.get("titleBlockHeight", 0)

    print(f"\n   SHEET BOUNDARIES (NOW I CAN SEE!):")
    print(f"      Total sheet size: {sheet_width_in:.1f}\" x {sheet_height_in:.1f}\"")
    print(f"      ({sheet_width_ft:.2f}' x {sheet_height_ft:.2f}')")

    if drawing_width_ft > 0:
        print(f"\n   AVAILABLE DRAWING AREA:")
        print(f"      Drawing area: {drawing_width_in:.1f}\" x {drawing_height_in:.1f}\"")
        print(f"      ({drawing_width_ft:.2f}' x {drawing_height_ft:.2f}')")
        print(f"      Title block height: {title_block_height*12:.1f}\"")
    else:
        print(f"\n   [WARNING] Could not detect drawing area")

    # Get viewports
    print("\n[STEP 3] Analyzing viewports on sheet...")
    vp_result = client.send_request("getViewportBounds", {
        "sheetId": sheet_id
    })

    if not vp_result.get("success"):
        print(f"ERROR: {vp_result.get('error')}")
        return

    viewports = vp_result.get("viewports", [])
    print(f"   Found {len(viewports)} viewport(s)")

    if not viewports:
        print("   No viewports to analyze")
        return

    # Analyze each viewport
    for i, vp in enumerate(viewports, 1):
        vp_id = vp.get("viewportId")
        view_id = vp.get("viewId")
        view_name = vp.get("viewName")
        current_scale = vp.get("viewScale")
        vp_width_ft = vp.get("width")
        vp_height_ft = vp.get("height")
        vp_width_in = vp_width_ft * 12
        vp_height_in = vp_height_ft * 12
        center = vp.get("center")

        print(f"\n   Viewport {i}: {view_name}")
        print(f"      Current scale: 1/{current_scale}\"")
        print(f"      Size: {vp_width_in:.1f}\" x {vp_height_in:.1f}\"")
        print(f"      Position: ({center[0]:.2f}, {center[1]:.2f})")

        # Check if it fits in the drawing area
        if drawing_width_ft > 0:
            width_usage = (vp_width_ft / drawing_width_ft) * 100
            height_usage = (vp_height_ft / drawing_height_ft) * 100

            print(f"\n      FIT ANALYSIS:")
            print(f"         Width: {vp_width_in:.1f}\" of {drawing_width_in:.1f}\" available ({width_usage:.0f}%)")
            print(f"         Height: {vp_height_in:.1f}\" of {drawing_height_in:.1f}\" available ({height_usage:.0f}%)")

            needs_adjustment = False
            recommended_scale = current_scale

            if width_usage > 90 or height_usage > 90:
                print(f"\n      [ISSUE] Viewport uses >{90}% of available space - TOO TIGHT!")
                needs_adjustment = True
            elif width_usage > 100 or height_usage > 100:
                print(f"\n      [CRITICAL] Viewport EXCEEDS drawing area!")
                needs_adjustment = True

            if width_usage < 50 and height_usage < 50:
                print(f"\n      [NOTE] Viewport is small - could use larger scale for readability")
                # Recommend a larger scale (smaller number = bigger drawing)
                recommended_scale = max(current_scale // 2, 16)  # At least 1/16" scale

            if needs_adjustment:
                # Calculate optimal scale targeting 70-80% usage
                target_usage = 0.75  # 75% of available space

                # Calculate scale based on which dimension is more constrained
                scale_for_width = int((vp_width_ft / (drawing_width_ft * target_usage)) * current_scale)
                scale_for_height = int((vp_height_ft / (drawing_height_ft * target_usage)) * current_scale)

                calc_scale = max(scale_for_width, scale_for_height)

                # Round to standard scales
                standard_scales = [16, 24, 32, 48, 64, 96, 128, 192, 256, 384]
                recommended_scale = min(standard_scales, key=lambda x: abs(x - calc_scale))

                print(f"\n      RECOMMENDED ADJUSTMENT:")
                print(f"         Current scale: 1/{current_scale}\"")
                print(f"         Recommended: 1/{recommended_scale}\" (targets 75% usage)")

                # Apply the scale
                print(f"\n      [STEP 4] Applying scale 1/{recommended_scale}\"...")

                set_scale_result = client.send_request("setViewScale", {
                    "viewId": view_id,
                    "scale": recommended_scale
                })

                if set_scale_result.get("success"):
                    print(f"         [OK] Scale applied!")

                    # Verify the result
                    verify_result = client.send_request("getViewportBounds", {
                        "sheetId": sheet_id
                    })

                    if verify_result.get("success"):
                        new_vps = verify_result.get("viewports", [])
                        for new_vp in new_vps:
                            if new_vp.get("viewId") == view_id:
                                new_width_in = new_vp.get("width") * 12
                                new_height_in = new_vp.get("height") * 12
                                new_scale = new_vp.get("viewScale")

                                new_width_usage = (new_vp.get("width") / drawing_width_ft) * 100
                                new_height_usage = (new_vp.get("height") / drawing_height_ft) * 100

                                print(f"\n         RESULT:")
                                print(f"            New size: {new_width_in:.1f}\" x {new_height_in:.1f}\"")
                                print(f"            New scale: 1/{new_scale}\"")
                                print(f"            Width usage: {new_width_usage:.0f}%")
                                print(f"            Height usage: {new_height_usage:.0f}%")

                                if new_width_usage <= 85 and new_height_usage <= 85:
                                    print(f"\n            [SUCCESS] Viewport now fits properly!")
                                    print(f"            Clean layout with {100-max(new_width_usage, new_height_usage):.0f}% margin")
                                else:
                                    print(f"\n            [INFO] Viewport still uses {max(new_width_usage, new_height_usage):.0f}% of space")
                else:
                    print(f"         [ERROR] {set_scale_result.get('error')}")
            else:
                print(f"\n      [OK] Viewport fits well in drawing area!")

    print("\n" + "=" * 80)
    print("SHEET ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nKey Learning:")
    print(f"  - Sheet size: {sheet_width_in:.1f}\" x {sheet_height_in:.1f}\"")
    if drawing_width_ft > 0:
        print(f"  - Drawing area: {drawing_width_in:.1f}\" x {drawing_height_in:.1f}\"")
        print(f"  - I can now SEE the sheet boundaries properly!")
        print(f"  - Target 70-80% usage for clean, readable layouts")
    print("=" * 80)

if __name__ == "__main__":
    main()
