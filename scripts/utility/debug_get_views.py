"""
Debug script to see what getViews actually returns
"""
import sys
import json
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("DEBUG: Testing getViews Response Structure")
    print("=" * 80)

    client = RevitClient()

    print("\nCalling getViews...")
    result = client.send_request("getViews", {})

    print("\nRaw Response:")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 80)
    print("Parsing Response...")
    print("=" * 80)

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")
        return

    print(f"Success: {result.get('success')}")

    # Try different paths to get views
    print("\nTrying result.get('views'):")
    views1 = result.get("views", [])
    print(f"  Found {len(views1)} views")

    print("\nTrying result.get('result', {}).get('views'):")
    views_data = result.get("result", {})
    views2 = views_data.get("views", [])
    print(f"  Found {len(views2)} views")

    if views2:
        print(f"\nFirst 3 views:")
        for i, view in enumerate(views2[:3]):
            print(f"  {i+1}. {view}")

        # Filter for floor plans
        floor_plans = [v for v in views2 if v.get("viewType") == "FloorPlan"]
        print(f"\nFloor plans found: {len(floor_plans)}")
        for fp in floor_plans[:5]:
            print(f"  - {fp.get('name')} (ID: {fp.get('id')})")

if __name__ == "__main__":
    main()
