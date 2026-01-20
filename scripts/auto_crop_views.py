#!/usr/bin/env python3
"""
Automatic view cropping and scaling like an architect would do.
Analyzes building extents, determines appropriate scales, and sets crop boxes.
"""

import subprocess
import json
import time

def send_mcp(method, params=None):
    """Send MCP command to Revit via named pipe."""
    request = {'method': method}
    if params:
        request['params'] = params

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
    output = result.stdout.strip()
    json_start = output.find('{')
    if json_start >= 0:
        output = output[json_start:]
    try:
        return json.loads(output)
    except:
        return {"success": False, "error": output or result.stderr.strip()}


def calculate_building_extents(walls):
    """Calculate the bounding box of all walls."""
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    for wall in walls:
        start = wall.get('startPoint', {})
        end = wall.get('endPoint', {})

        for pt in [start, end]:
            x, y = pt.get('x', 0), pt.get('y', 0)
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

    return {
        'min_x': min_x,
        'max_x': max_x,
        'min_y': min_y,
        'max_y': max_y,
        'width': max_x - min_x,
        'height': max_y - min_y,
        'center_x': (min_x + max_x) / 2,
        'center_y': (min_y + max_y) / 2
    }


def calculate_scale_for_sheet(content_width, content_height, sheet_width=32, sheet_height=20):
    """
    Calculate appropriate scale to fit content on sheet.
    Sheet dimensions in inches (usable area on ARCH D).
    Returns Revit scale factor (e.g., 48 for 1/4" = 1'-0").

    Common architectural scales:
    - 1" = 1'-0"   -> scale 12
    - 3/4" = 1'-0" -> scale 16
    - 1/2" = 1'-0" -> scale 24
    - 3/8" = 1'-0" -> scale 32
    - 1/4" = 1'-0" -> scale 48
    - 3/16" = 1'-0" -> scale 64
    - 1/8" = 1'-0" -> scale 96
    - 1" = 10'-0"  -> scale 120
    - 1" = 20'-0"  -> scale 240
    """
    # Content in feet, sheet in inches
    # At scale S: 1 inch on paper = S/12 feet in model
    # Required paper width = content_width / (S/12) = content_width * 12 / S inches

    standard_scales = [12, 16, 24, 32, 48, 64, 96, 120, 240]

    for scale in standard_scales:
        paper_width = content_width * 12 / scale
        paper_height = content_height * 12 / scale

        if paper_width <= sheet_width and paper_height <= sheet_height:
            return scale

    return standard_scales[-1]  # Return largest scale if nothing fits


def get_view_type_scale(view_type, building_size):
    """
    Determine appropriate scale based on view type and building size.
    This is how an architect would think about scale selection.
    """
    width, height = building_size

    if 'ENLARGED' in view_type.upper():
        # Enlarged plans: 1/2" or 3/8" = 1'-0"
        return 24  # 1/2" = 1'-0" for detail views

    elif 'ROOF' in view_type.upper():
        # Roof plans: typically smaller scale
        return calculate_scale_for_sheet(width * 1.2, height * 1.2)

    elif 'SITE' in view_type.upper() or 'LANDSCAPE' in view_type.upper() or 'IRRIGATION' in view_type.upper():
        # Site-related: much smaller scale
        return 96  # 1/8" = 1'-0" or smaller

    elif 'FLOOR' in view_type.upper() or 'PLAN' in view_type.upper():
        # Floor plans: 1/4" typically
        return calculate_scale_for_sheet(width * 1.15, height * 1.15)

    elif 'COLUMN' in view_type.upper():
        # Structural plans similar to floor plans
        return calculate_scale_for_sheet(width * 1.15, height * 1.15)

    else:
        # Default
        return 48


def estimate_room_zones(walls, extents):
    """
    Estimate bathroom and kitchen zones from interior wall patterns.
    This is a simplified heuristic - a real system would use room boundaries.
    """
    # For this building, based on wall analysis:
    # Interior walls suggest bathroom area is in the SW quadrant
    # Kitchen area is typically near the main living space

    center_x = extents['center_x']
    center_y = extents['center_y']

    # Estimate bathroom zone (usually smaller, in corner)
    # Looking at interior walls around x: -12 to 0, y: -9 to 4
    bathroom_zone = {
        'min_x': -14,
        'max_x': 2,
        'min_y': -14,
        'max_y': 6,
        'name': 'BATHROOM AREA'
    }

    # Estimate kitchen zone (usually along exterior wall with cabinets)
    # Looking at wall patterns, kitchen might be around x: -24 to -8, y: -9 to 14
    kitchen_zone = {
        'min_x': -26,
        'max_x': -6,
        'min_y': -10,
        'max_y': 16,
        'name': 'KITCHEN AREA'
    }

    return bathroom_zone, kitchen_zone


def main():
    print("=" * 70)
    print("AUTOMATIC VIEW CROPPING AND SCALING")
    print("=" * 70)

    # Step 1: Get walls and calculate extents
    print("\n[1] Analyzing building geometry...")
    walls_data = send_mcp('getWalls')
    if not walls_data.get('success'):
        print(f"ERROR: Could not get walls: {walls_data.get('error')}")
        return

    walls = walls_data.get('walls', [])
    extents = calculate_building_extents(walls)

    print(f"    Building extents:")
    print(f"      Width:  {extents['width']:.1f} feet")
    print(f"      Height: {extents['height']:.1f} feet")
    print(f"      X range: {extents['min_x']:.1f} to {extents['max_x']:.1f}")
    print(f"      Y range: {extents['min_y']:.1f} to {extents['max_y']:.1f}")

    # Step 2: Get all views
    print("\n[2] Getting views...")
    views_data = send_mcp('getViews')
    if not views_data.get('success'):
        print(f"ERROR: Could not get views: {views_data.get('error')}")
        return

    views = views_data.get('result', {}).get('views', [])

    # Create view lookup
    view_lookup = {}
    for v in views:
        view_lookup[v['id']] = v
        view_lookup[v['name']] = v

    # Step 3: Define crop regions and scales for each view type
    print("\n[3] Calculating crop regions and scales...")

    # Add margin around building (10% on each side)
    margin = max(extents['width'], extents['height']) * 0.10

    # Full building crop box with margin
    full_building_crop = [
        [extents['min_x'] - margin, extents['min_y'] - margin, -10],
        [extents['max_x'] + margin, extents['max_y'] + margin, 50]
    ]

    # Estimate room zones for enlarged views
    bathroom_zone, kitchen_zone = estimate_room_zones(walls, extents)

    # Bathroom crop (smaller area, more margin proportionally)
    bathroom_margin = 3  # 3 feet margin
    bathroom_crop = [
        [bathroom_zone['min_x'] - bathroom_margin, bathroom_zone['min_y'] - bathroom_margin, -2],
        [bathroom_zone['max_x'] + bathroom_margin, bathroom_zone['max_y'] + bathroom_margin, 15]
    ]

    # Kitchen crop
    kitchen_margin = 3
    kitchen_crop = [
        [kitchen_zone['min_x'] - kitchen_margin, kitchen_zone['min_y'] - kitchen_margin, -2],
        [kitchen_zone['max_x'] + kitchen_margin, kitchen_zone['max_y'] + kitchen_margin, 15]
    ]

    # Site plan - larger area
    site_margin = 20  # 20 feet for site context
    site_crop = [
        [extents['min_x'] - site_margin, extents['min_y'] - site_margin, -10],
        [extents['max_x'] + site_margin, extents['max_y'] + site_margin, 50]
    ]

    # Views to configure
    view_configs = [
        # (view_name, crop_box, scale, description)
        ('FLOOR PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('ROOF PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('COLUMN PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('ENLARGED BATHROOM PLAN', bathroom_crop, 24, '1/2" = 1\'-0"'),
        ('ENLARGED KITCHEN PLAN', kitchen_crop, 24, '1/2" = 1\'-0"'),
        ('SITE PLAN', site_crop, 96, '1/8" = 1\'-0"'),
        ('LANDSCAPE PLAN', site_crop, 96, '1/8" = 1\'-0"'),
        ('IRRIGATION PLAN', site_crop, 96, '1/8" = 1\'-0"'),
        ('MECHANICAL PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('ELECTRICAL POWER PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('ELECTRICAL LIGHTING PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('PLUMBING PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('FOUNDATION PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
        ('ROOF FRAMING PLAN', full_building_crop, 48, '1/4" = 1\'-0"'),
    ]

    # Step 4: Apply crop boxes and scales
    print("\n[4] Applying crop boxes and scales...")

    for view_name, crop_box, scale, scale_desc in view_configs:
        if view_name in view_lookup:
            view_id = view_lookup[view_name]['id']

            # Set scale first
            scale_result = send_mcp('setViewScale', {'viewId': view_id, 'scale': scale})
            if scale_result.get('success'):
                print(f"    {view_name}: Scale set to {scale} ({scale_desc})")
            else:
                print(f"    {view_name}: Scale ERROR - {scale_result.get('error')}")

            time.sleep(0.2)

            # Set crop box
            crop_result = send_mcp('setViewCropBox', {
                'viewId': view_id,
                'enableCrop': True,
                'cropBox': crop_box
            })
            if crop_result.get('success'):
                crop_width = crop_box[1][0] - crop_box[0][0]
                crop_height = crop_box[1][1] - crop_box[0][1]
                print(f"             Crop box: {crop_width:.0f}' x {crop_height:.0f}'")
            else:
                print(f"             Crop ERROR - {crop_result.get('error')}")

            time.sleep(0.2)
        else:
            print(f"    {view_name}: NOT FOUND")

    # Step 5: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nBuilding: {extents['width']:.0f}' x {extents['height']:.0f}'")
    print(f"\nView configurations applied:")
    print("  - Full building views: 1/4\" = 1'-0\" (scale 48)")
    print("  - Enlarged plans: 1/2\" = 1'-0\" (scale 24)")
    print("  - Site plans: 1/8\" = 1'-0\" (scale 96)")
    print("\nAll crop boxes include appropriate margins.")
    print("\nNote: Enlarged plan crop regions are estimates.")
    print("      Manual adjustment may be needed for exact room boundaries.")


if __name__ == '__main__':
    main()
