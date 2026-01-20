"""
Diagnose title block parameters to find the correct parameter names
"""
import sys
import json
sys.path.insert(0, r'D:\revit-mcp-server')

from revit_mcp_server.revit_client import RevitClient

def main():
    print("\n" + "=" * 80)
    print("DIAGNOSING TITLE BLOCK PARAMETERS")
    print("=" * 80)

    client = RevitClient()

    # Get the NTB 24X36 title block specifically
    print("\n[1] Getting all title blocks...")
    result = client.send_request("getTitleblockTypes", {})

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")
        return

    titleblocks = result.get("titleblocks", [])

    # Find the 24x36 one
    tb_24x36 = None
    for tb in titleblocks:
        if "24" in tb.get("typeName", "") and "36" in tb.get("typeName", ""):
            tb_24x36 = tb
            break

    if not tb_24x36:
        print("Could not find 24x36 title block, using first one")
        tb_24x36 = titleblocks[0]

    print(f"\nTitle Block: {tb_24x36.get('familyName')} - {tb_24x36.get('typeName')}")
    print(f"ID: {tb_24x36.get('titleblockId')}")

    # Now I need to get ALL parameters for this title block
    # Let me use a different approach - get the element and query all its parameters
    print(f"\n[2] Getting all parameters for this title block...")
    print(f"    (This will help me find the correct parameter names)")

    # I'll need to create a new method to get all parameters
    # For now, let me check what the actual sheet size is by creating a test sheet
    print(f"\n[3] Creating test sheet to check actual size...")

    sheet_result = client.send_request("createSheet", {
        "sheetNumber": "DIAG-TEST-01",
        "sheetName": "Diagnostic Test Sheet",
        "titleblockId": tb_24x36.get("titleblockId")
    })

    if sheet_result.get("success"):
        sheet_id = sheet_result.get("sheetId")
        print(f"    [OK] Test sheet created (ID: {sheet_id})")

        # Now analyze this sheet to get its actual dimensions
        analyze_result = client.send_request("analyzeSheetLayout", {
            "sheetId": sheet_id
        })

        if analyze_result.get("success"):
            width_ft = analyze_result.get("sheetWidth", 0)
            height_ft = analyze_result.get("sheetHeight", 0)
            width_in = width_ft * 12
            height_in = height_ft * 12

            print(f"\n    ACTUAL SHEET SIZE FROM TITLE BLOCK:")
            print(f"      Width: {width_ft:.3f} feet = {width_in:.1f} inches")
            print(f"      Height: {height_ft:.3f} feet = {height_in:.1f} inches")

            if width_in > 20 and height_in > 30:
                print(f"\n    [OK] This IS a large format sheet!")
                print(f"    Available drawing area: ~{width_in-6:.0f}\" x {height_in-6:.0f}\"")
            else:
                print(f"\n    [WARN] This appears to be a smaller sheet")

    print("\n" + "=" * 80)
    print("KEY FINDINGS:")
    print("=" * 80)
    print(f"\nTitle blocks found: {len(titleblocks)}")
    for tb in titleblocks:
        name = f"{tb.get('familyName')} - {tb.get('typeName')}"
        if "24" in name or "30" in name or "34" in name or "44" in name:
            print(f"  Large format: {name} (ID: {tb.get('titleblockId')})")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
