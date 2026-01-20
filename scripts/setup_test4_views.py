#!/usr/bin/env python3
"""
Setup TEST-4 views to match 1700 Sheffield structure.
Creates missing views, renames to Sheffield convention, sets crop regions, places on sheets.
"""

import subprocess
import json
import time

def send_mcp(method, params=None):
    """Send MCP command to Revit via named pipe."""
    request = {'method': method}
    if params:
        request['params'] = params  # Note: MCP server expects 'params' not 'parameters'

    ps_script = f'''
$pipeName = 'RevitMCPBridge2026'
$request = @'
{json.dumps(request)}
'@

try {{
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(15000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.WriteLine($request)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    Write-Output $response
}} catch {{
    Write-Output ('{{"success": false, "error": "' + $_.Exception.Message + '"}}')
}}
'''
    result = subprocess.run(['powershell.exe', '-Command', ps_script],
                          capture_output=True, text=True, timeout=30)
    # Extract JSON from output (may have shell messages prepended)
    output = result.stdout.strip()
    # Find the JSON object in the output
    json_start = output.find('{')
    if json_start >= 0:
        output = output[json_start:]
    try:
        return json.loads(output)
    except:
        return {"success": False, "error": output or result.stderr.strip()}

def create_floor_plan(level_id, view_name):
    """Create a floor plan view."""
    result = send_mcp('createFloorPlan', {
        'levelId': level_id,
        'viewName': view_name
    })
    if result.get('success'):
        print(f"  Created: {view_name} (ID: {result.get('viewId')})")
    else:
        print(f"  ERROR creating {view_name}: {result.get('error')}")
    return result

def rename_view(view_id, new_name):
    """Rename a view."""
    result = send_mcp('renameView', {
        'viewId': view_id,
        'newName': new_name
    })
    if result.get('success'):
        print(f"  Renamed view {view_id} to: {new_name}")
    else:
        print(f"  ERROR renaming view {view_id}: {result.get('error')}")
    return result

def set_crop_box(view_id, enable=True, crop_box=None):
    """Set crop box on view."""
    params = {'viewId': view_id, 'enableCrop': enable}
    if crop_box:
        params['cropBox'] = crop_box
    result = send_mcp('setViewCropBox', params)
    if result.get('success'):
        print(f"  Set crop box on view {view_id}")
    else:
        print(f"  ERROR setting crop box: {result.get('error')}")
    return result

def place_view_on_sheet(sheet_id, view_id, x=1.0, y=1.0):
    """Place view on sheet at position."""
    result = send_mcp('placeViewOnSheet', {
        'sheetId': sheet_id,
        'viewId': view_id,
        'x': x,
        'y': y
    })
    if result.get('success'):
        print(f"  Placed view {view_id} on sheet {sheet_id}")
    else:
        print(f"  ERROR placing view: {result.get('error')}")
    return result

def create_legend(legend_name):
    """Create a legend view."""
    result = send_mcp('createLegendView', {
        'viewName': legend_name
    })
    if result.get('success'):
        print(f"  Created legend: {legend_name} (ID: {result.get('viewId')})")
    else:
        print(f"  ERROR creating legend: {result.get('error')}")
    return result

def duplicate_view(view_id, new_name, option='Duplicate'):
    """Duplicate a view."""
    result = send_mcp('duplicateView', {
        'viewId': view_id,
        'newName': new_name,
        'duplicateOption': option
    })
    if result.get('success'):
        print(f"  Duplicated view to: {new_name} (ID: {result.get('newViewId')})")
    else:
        print(f"  ERROR duplicating view: {result.get('error')}")
    return result

def main():
    print("=" * 60)
    print("Setting up TEST-4 views to match 1700 Sheffield")
    print("=" * 60)

    # Get current state
    print("\n[1] Getting current project state...")
    levels = send_mcp('getLevels')
    views = send_mcp('getViews')
    sheets = send_mcp('getAllSheets')

    if not levels.get('success'):
        print(f"ERROR: Could not get levels: {levels.get('error')}")
        return

    print(f"  Levels: {levels.get('levelCount')}")
    print(f"  Views: {views.get('result', {}).get('count', 0)}")
    print(f"  Sheets: {sheets.get('result', {}).get('totalSheets', 0)}")

    # Map levels
    level_map = {l['name']: l['levelId'] for l in levels.get('levels', [])}
    print(f"  Level map: {level_map}")

    # Map sheets by number
    sheet_map = {s['sheetNumber']: s for s in sheets.get('result', {}).get('sheets', [])}

    # Map views by name
    view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}

    # === STEP 2: Rename existing views to Sheffield naming ===
    print("\n[2] Renaming views to Sheffield naming convention...")

    # Sheffield naming:
    # - FLOOR PLAN (not "L1 - Architectural")
    # - REAR EXTERIOR ELEVATION, FRONT EXTERIOR ELEVATION, etc.
    # - ROOF PLAN
    # - SITE PLAN

    view_renames = [
        # (current_name, new_name)
        ('L1 - Architectural', 'REFLECTED CEILING PLAN'),  # ceiling plan
        ('L2 - Architectural', 'SECOND FLOOR PLAN'),
        ('L2 - Architectural', 'SECOND FLOOR REFLECTED CEILING'),  # ceiling version
        ('Cover Sheet View', '3D VIEW'),
        ('L1 - MECHANICAL', 'MECHANICAL PLAN'),
        ('L1 - ELECTRICAL POWER', 'ELECTRICAL POWER PLAN'),
        ('L1 - ELECTRICAL LIGHTING', 'ELECTRICAL LIGHTING PLAN'),
        ('L1 - PLUMBING', 'PLUMBING PLAN'),
        ('L2 - PLUMBING', 'SECOND FLOOR PLUMBING PLAN'),
        ('{3D}', 'DEFAULT 3D VIEW'),
    ]

    for current_name, new_name in view_renames:
        if current_name in view_map:
            result = rename_view(view_map[current_name]['id'], new_name)
            time.sleep(0.3)  # Small delay between operations

    # === STEP 3: Create missing views ===
    print("\n[3] Creating missing views...")

    # Create ROOF PLAN if it doesn't exist
    if 'ROOF PLAN' not in view_map:
        # Use L2 level for roof plan
        l2_id = level_map.get('L2')
        if l2_id:
            result = create_floor_plan(l2_id, 'ROOF PLAN')
            time.sleep(0.5)

    # Create legends for A-0.0 sheet
    legends_to_create = [
        'ABBREVIATIONS',
        'SYMBOLS',
        'GENERAL NOTES',
        'PLAN LEGEND'
    ]

    for legend_name in legends_to_create:
        if legend_name not in view_map:
            result = create_legend(legend_name)
            time.sleep(0.3)

    # Create enlarged plans for A-5.0 (duplicate from FLOOR PLAN)
    if 'FLOOR PLAN' in view_map:
        enlarged_plans = [
            'ENLARGED BATHROOM PLAN',
            'ENLARGED KITCHEN PLAN',
            'ENLARGED ENTRY PLAN'
        ]
        for plan_name in enlarged_plans:
            if plan_name not in view_map:
                result = duplicate_view(view_map['FLOOR PLAN']['id'], plan_name, 'Duplicate')
                time.sleep(0.3)

    # === STEP 4: Enable crop on key views ===
    print("\n[4] Setting crop regions on views...")

    # Refresh views list
    views = send_mcp('getViews')
    view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}

    views_to_crop = [
        'FLOOR PLAN',
        'ROOF PLAN',
        'SITE PLAN',
        'FRONT EXTERIOR ELEVATION',
        'REAR EXTERIOR ELEVATION',
        'LEFT-SIDE EXTERIOR ELEVATION',
        'RIGHT-SIDE EXTERIOR ELEVATION',
        'BUILDING SECTION - AA'
    ]

    for view_name in views_to_crop:
        if view_name in view_map:
            result = set_crop_box(view_map[view_name]['id'], enable=True)
            time.sleep(0.2)

    # === STEP 5: Place views on empty sheets ===
    print("\n[5] Placing views on empty sheets...")

    # Refresh data
    sheets = send_mcp('getAllSheets')
    views = send_mcp('getViews')
    sheet_map = {s['sheetNumber']: s for s in sheets.get('result', {}).get('sheets', [])}
    view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}

    # Sheet A-0.0: GENERAL NOTES / SITE DATA - place legends
    if 'A-0.0' in sheet_map and sheet_map['A-0.0']['viewCount'] == 0:
        sheet_id = sheet_map['A-0.0']['id']
        # Place legends in a grid
        positions = [(0.5, 1.5), (1.5, 1.5), (0.5, 0.7), (1.5, 0.7)]
        for i, legend_name in enumerate(['ABBREVIATIONS', 'SYMBOLS', 'GENERAL NOTES', 'PLAN LEGEND']):
            if legend_name in view_map and i < len(positions):
                x, y = positions[i]
                place_view_on_sheet(sheet_id, view_map[legend_name]['id'], x, y)
                time.sleep(0.3)

    # Sheet A-3.0: ROOF PLAN & DETAILS
    if 'A-3.0' in sheet_map and sheet_map['A-3.0']['viewCount'] == 0:
        sheet_id = sheet_map['A-3.0']['id']
        if 'ROOF PLAN' in view_map:
            place_view_on_sheet(sheet_id, view_map['ROOF PLAN']['id'], 1.2, 1.0)
            time.sleep(0.3)

    # Sheet A-5.0: ENLARGED PLANS
    if 'A-5.0' in sheet_map and sheet_map['A-5.0']['viewCount'] == 0:
        sheet_id = sheet_map['A-5.0']['id']
        positions = [(0.7, 1.2), (1.5, 1.2), (0.7, 0.5)]
        for i, plan_name in enumerate(['ENLARGED BATHROOM PLAN', 'ENLARGED KITCHEN PLAN', 'ENLARGED ENTRY PLAN']):
            if plan_name in view_map and i < len(positions):
                x, y = positions[i]
                place_view_on_sheet(sheet_id, view_map[plan_name]['id'], x, y)
                time.sleep(0.3)

    # Sheet S-3.0: COLUMN & BOND BEAM PLAN
    if 'S-3.0' in sheet_map and sheet_map['S-3.0']['viewCount'] == 0:
        sheet_id = sheet_map['S-3.0']['id']
        # Create a structural plan if needed
        l1_id = level_map.get('L1')
        if l1_id and 'COLUMN PLAN' not in view_map:
            result = create_floor_plan(l1_id, 'COLUMN PLAN')
            time.sleep(0.5)
            # Refresh and place
            views = send_mcp('getViews')
            view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}
            if 'COLUMN PLAN' in view_map:
                place_view_on_sheet(sheet_id, view_map['COLUMN PLAN']['id'], 1.2, 1.0)

    # Sheet L-1.0: LANDSCAPE PLAN
    if 'L-1.0' in sheet_map and sheet_map['L-1.0']['viewCount'] == 0:
        sheet_id = sheet_map['L-1.0']['id']
        if 'SITE PLAN' in view_map:
            # Duplicate site plan for landscape
            result = duplicate_view(view_map['SITE PLAN']['id'], 'LANDSCAPE PLAN', 'Duplicate')
            time.sleep(0.5)
            views = send_mcp('getViews')
            view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}
            if 'LANDSCAPE PLAN' in view_map:
                place_view_on_sheet(sheet_id, view_map['LANDSCAPE PLAN']['id'], 1.2, 1.0)

    # Sheet L-2.0: IRRIGATION PLAN
    if 'L-2.0' in sheet_map and sheet_map['L-2.0']['viewCount'] == 0:
        sheet_id = sheet_map['L-2.0']['id']
        if 'SITE PLAN' in view_map:
            result = duplicate_view(view_map['SITE PLAN']['id'], 'IRRIGATION PLAN', 'Duplicate')
            time.sleep(0.5)
            views = send_mcp('getViews')
            view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}
            if 'IRRIGATION PLAN' in view_map:
                place_view_on_sheet(sheet_id, view_map['IRRIGATION PLAN']['id'], 1.2, 1.0)

    # === STEP 6: Final summary ===
    print("\n[6] Final summary...")
    sheets = send_mcp('getAllSheets')
    views = send_mcp('getViews')

    print(f"\n  Total views: {views.get('result', {}).get('count', 0)}")
    print(f"  Total sheets: {sheets.get('result', {}).get('totalSheets', 0)}")

    print("\n  Sheets with views:")
    for s in sorted(sheets.get('result', {}).get('sheets', []), key=lambda x: x['sheetNumber']):
        status = "OK" if s['viewCount'] > 0 else "EMPTY"
        print(f"    {s['sheetNumber']}: {s['sheetName']} - {s['viewCount']} views [{status}]")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == '__main__':
    main()
