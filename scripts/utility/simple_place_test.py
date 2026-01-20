"""
Simple test - place ONE existing view on ONE new sheet
"""
import sys
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("SIMPLE TEST: Place ONE view on ONE sheet")
    print("=" * 80)

    client = RevitClient()

    # Get existing views
    print("\n[1] Getting existing views...")
    result = client.send_request("getViews", {})

    if not result.get("success"):
        print(f"   ERROR: {result.get('error')}")
        return

    views_data = result.get("result", {})
    views = views_data.get("views", [])

    floor_plans = [v for v in views if v.get("viewType") == "FloorPlan" and v.get("level")]

    if not floor_plans:
        print("   ERROR: No floor plans found!")
        return

    # Use first floor plan
    view = floor_plans[0]
    view_name = view.get("name")
    view_id = view.get("id")

    print(f"   [OK] Found view: {view_name} (ID: {view_id})")

    # Create sheet
    print("\n[2] Creating sheet...")
    sheet_num = "SIMPLE-TEST-01"
    sheet_result = client.send_request("createSheet", {
        "sheetNumber": sheet_num,
        "sheetName": "Simple Placement Test"
    })

    print(f"   Response: {sheet_result}")

    if not sheet_result.get("success"):
        print(f"   ERROR: {sheet_result.get('error')}")
        return

    sheet_id = sheet_result.get("sheetId")
    print(f"   [OK] Sheet created (ID: {sheet_id})")

    # Place view on sheet
    print("\n[3] Placing view on sheet...")
    print(f"   sheetId: {sheet_id}")
    print(f"   viewId: {view_id}")
    print(f"   location: [1.5, 1.0]")

    place_result = client.send_request("placeViewOnSheet", {
        "sheetId": sheet_id,
        "viewId": view_id,
        "location": [1.5, 1.0]
    })

    print(f"\n   Response: {place_result}")

    if place_result.get("success"):
        print("\n" + "=" * 80)
        print("SUCCESS! VIEW IS ON THE SHEET!")
        print("=" * 80)
        print(f"\nGo to Revit and open sheet '{sheet_num}'")
        print(f"You should see '{view_name}' placed on it!")
        print("=" * 80)
    else:
        print(f"\n   ERROR: {place_result.get('error')}")

if __name__ == "__main__":
    main()
