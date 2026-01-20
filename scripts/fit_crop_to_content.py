#!/usr/bin/env python3
"""
Resize crop boxes to fit building content tightly.
Uses actual building geometry to set proper crop dimensions.
"""

import subprocess
import json
import time

def send_mcp(method, params=None):
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


def main():
    print("=" * 70)
    print("FITTING CROP BOXES TO BUILDING CONTENT")
    print("=" * 70)

    # Get building geometry
    print("\n[1] Getting building extents...")
    walls_data = send_mcp('getWalls')
    walls = walls_data.get('walls', [])
    
    # Calculate extents
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = 0, 0
    
    for wall in walls:
        for pt in [wall.get('startPoint', {}), wall.get('endPoint', {})]:
            x, y = pt.get('x', 0), pt.get('y', 0)
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
        
        base = wall.get('baseOffset', 0)
        height = wall.get('height', 10)
        min_z = min(min_z, base)
        max_z = max(max_z, base + height)
    
    width = max_x - min_x  # ~56'
    depth = max_y - min_y  # ~50'
    height = max_z - min_z  # ~14'
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    print(f"    Building: {width:.0f}' x {depth:.0f}' x {height:.0f}'")
    print(f"    X: {min_x:.1f} to {max_x:.1f}, center: {center_x:.1f}")
    print(f"    Y: {min_y:.1f} to {max_y:.1f}, center: {center_y:.1f}")
    print(f"    Z: {min_z:.1f} to {max_z:.1f}")

    # Get views
    views_data = send_mcp('getViews')
    views = views_data.get('result', {}).get('views', [])
    view_map = {v['name']: v for v in views}

    # Margins for crop boxes
    plan_margin = 5  # 5' margin for plans
    elev_h_margin = 3  # 3' horizontal margin for elevations
    elev_v_margin_bottom = 2  # 2' below grade
    elev_v_margin_top = 3  # 3' above roof

    print("\n[2] Setting tight crop boxes...")
    
    # FLOOR PLANS - crop to building footprint + margin
    plan_views = ['FLOOR PLAN', 'ROOF PLAN', 'COLUMN PLAN', 'SITE PLAN', 
                  'MECHANICAL PLAN', 'ELECTRICAL POWER PLAN', 
                  'ELECTRICAL LIGHTING PLAN', 'PLUMBING PLAN',
                  'FOUNDATION PLAN', 'ROOF FRAMING PLAN',
                  'LANDSCAPE PLAN', 'IRRIGATION PLAN']
    
    for view_name in plan_views:
        if view_name in view_map:
            view_id = view_map[view_name]['id']
            
            # Site plans get more margin
            margin = 15 if 'SITE' in view_name or 'LANDSCAPE' in view_name or 'IRRIGATION' in view_name else plan_margin
            
            crop_box = [
                [min_x - margin, min_y - margin, -10],
                [max_x + margin, max_y + margin, 50]
            ]
            
            result = send_mcp('setViewCropBox', {
                'viewId': view_id,
                'enableCrop': True,
                'cropBox': crop_box
            })
            
            crop_w = crop_box[1][0] - crop_box[0][0]
            crop_h = crop_box[1][1] - crop_box[0][1]
            
            if result.get('success'):
                print(f"    {view_name}: {crop_w:.0f}' x {crop_h:.0f}'")
            else:
                print(f"    {view_name}: ERROR - {result.get('error')}")
            
            time.sleep(0.2)

    # ELEVATIONS - need proper coordinate transformation
    # Front/Rear look along Y axis, so horizontal = X, vertical = Z
    # Left/Right look along X axis, so horizontal = Y, vertical = Z
    
    print("\n    --- Elevations ---")
    
    elev_configs = {
        'FRONT EXTERIOR ELEVATION': {
            # Looking from South (negative Y), horizontal is X
            'crop': [
                [min_x - elev_h_margin, min_z - elev_v_margin_bottom, min_y - 50],
                [max_x + elev_h_margin, max_z + elev_v_margin_top, max_y + 50]
            ]
        },
        'REAR EXTERIOR ELEVATION': {
            # Looking from North (positive Y), horizontal is X (reversed)
            'crop': [
                [min_x - elev_h_margin, min_z - elev_v_margin_bottom, min_y - 50],
                [max_x + elev_h_margin, max_z + elev_v_margin_top, max_y + 50]
            ]
        },
        'LEFT-SIDE EXTERIOR ELEVATION': {
            # Looking from East (positive X), horizontal is Y
            'crop': [
                [min_y - elev_h_margin, min_z - elev_v_margin_bottom, min_x - 50],
                [max_y + elev_h_margin, max_z + elev_v_margin_top, max_x + 50]
            ]
        },
        'RIGHT-SIDE EXTERIOR ELEVATION': {
            # Looking from West (negative X), horizontal is Y (reversed)
            'crop': [
                [min_y - elev_h_margin, min_z - elev_v_margin_bottom, min_x - 50],
                [max_y + elev_h_margin, max_z + elev_v_margin_top, max_x + 50]
            ]
        }
    }
    
    for view_name, config in elev_configs.items():
        if view_name in view_map:
            view_id = view_map[view_name]['id']
            crop_box = config['crop']
            
            result = send_mcp('setViewCropBox', {
                'viewId': view_id,
                'enableCrop': True,
                'cropBox': crop_box
            })
            
            crop_w = crop_box[1][0] - crop_box[0][0]
            crop_h = crop_box[1][1] - crop_box[0][1]
            
            if result.get('success'):
                print(f"    {view_name}: {crop_w:.0f}' x {crop_h:.0f}'")
            else:
                print(f"    {view_name}: ERROR - {result.get('error')}")
            
            time.sleep(0.2)

    # SECTIONS
    print("\n    --- Sections ---")
    
    if 'BUILDING SECTION - AA' in view_map:
        view_id = view_map['BUILDING SECTION - AA']['id']
        
        # Section crop - full building width and height
        crop_box = [
            [min_x - elev_h_margin, min_z - elev_v_margin_bottom, min_y - 5],
            [max_x + elev_h_margin, max_z + elev_v_margin_top, max_y + 5]
        ]
        
        result = send_mcp('setViewCropBox', {
            'viewId': view_id,
            'enableCrop': True,
            'cropBox': crop_box
        })
        
        if result.get('success'):
            print(f"    BUILDING SECTION - AA: {width + 2*elev_h_margin:.0f}' x {height + elev_v_margin_bottom + elev_v_margin_top:.0f}'")
        else:
            print(f"    BUILDING SECTION - AA: ERROR - {result.get('error')}")

    print("\n" + "=" * 70)
    print("COMPLETE - Crop boxes set to fit building content")
    print("=" * 70)


if __name__ == '__main__':
    main()
