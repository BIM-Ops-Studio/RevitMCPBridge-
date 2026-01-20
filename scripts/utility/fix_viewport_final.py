"""
Final fix for the North Elevation viewport
Adjust to 1/256" to fit properly
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("FINAL VIEWPORT FIT ADJUSTMENT")
    print("=" * 80)

    client = RevitClient()

    # Get active view
    active_result = client.send_request("getActiveView", {})
    if not active_result.get("success"):
        print(f"ERROR: {active_result.get('error')}")
        return

    sheet_id = active_result.get("viewId")

    # Get the viewport
    vp_result = client.send_request("getViewportBounds", {"sheetId": sheet_id})
    if not vp_result.get("success"):
        print(f"ERROR: {vp_result.get('error')}")
        return

    viewports = vp_result.get("viewports", [])
    if not viewports:
        print("No viewports found")
        return

    vp = viewports[0]
    view_id = vp.get("viewId")
    view_name = vp.get("viewName")
    current_scale = vp.get("viewScale")
    current_width = vp.get("width") * 12  # Convert to inches

    print(f"\nCurrent situation:")
    print(f"   View: {view_name}")
    print(f"   Scale: 1/{current_scale}\"")
    print(f"   Width: {current_width:.1f}\"")
    print(f"   Width vs 30\" available: {(current_width/30)*100:.0f}%")

    # Try 1/256" scale
    new_scale = 256
    print(f"\nApplying scale 1/{new_scale}\"...")

    set_scale_result = client.send_request("setViewScale", {
        "viewId": view_id,
        "scale": new_scale
    })

    if not set_scale_result.get("success"):
        print(f"   ERROR: {set_scale_result.get('error')}")
        return

    print(f"   [OK] Scale set to 1/{new_scale}\"")

    # Verify
    verify_result = client.send_request("getViewportBounds", {"sheetId": sheet_id})
    if verify_result.get("success"):
        new_vp = verify_result.get("viewports", [])[0]
        new_width = new_vp.get("width") * 12
        new_height = new_vp.get("height") * 12
        new_scale_check = new_vp.get("viewScale")

        print(f"\nNew situation:")
        print(f"   Scale: 1/{new_scale_check}\"")
        print(f"   Size: {new_width:.1f}\" x {new_height:.1f}\"")
        print(f"   Width vs 30\": {(new_width/30)*100:.0f}%")
        print(f"   Height vs 24\": {(new_height/24)*100:.0f}%")

        if new_width <= 30 and new_height <= 24:
            print(f"\n" + "=" * 80)
            print(f"SUCCESS! VIEW NOW FITS PROPERLY ON 24X36 SHEET!")
            print(f"=" * 80)
        else:
            print(f"\n   [INFO] View size: {new_width:.1f}\" x {new_height:.1f}\"")
            if new_width > 30:
                print(f"   Still {new_width - 30:.1f}\" too wide")

if __name__ == "__main__":
    main()
