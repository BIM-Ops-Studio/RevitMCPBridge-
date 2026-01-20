#!/usr/bin/env python3
"""
Fix crop regions - ensure crop is actually enabled and visible.
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


def main():
    print("=" * 70)
    print("CHECKING AND FIXING CROP REGIONS")
    print("=" * 70)

    # Get views
    print("\n[1] Getting views...")
    views_data = send_mcp('getViews')
    if not views_data.get('success'):
        print(f"ERROR: {views_data.get('error')}")
        return

    views = views_data.get('result', {}).get('views', [])
    
    # Check current crop status of key views
    test_views = [
        'FRONT EXTERIOR ELEVATION',
        'REAR EXTERIOR ELEVATION', 
        'LEFT-SIDE EXTERIOR ELEVATION',
        'RIGHT-SIDE EXTERIOR ELEVATION',
        'BUILDING SECTION - AA',
        'FLOOR PLAN',
        'ROOF PLAN'
    ]
    
    view_map = {v['name']: v for v in views}
    
    print("\n[2] Checking current crop status...")
    for name in test_views:
        if name in view_map:
            v = view_map[name]
            crop_active = v.get('cropBoxActive', 'unknown')
            crop_visible = v.get('cropBoxVisible', 'unknown')
            print(f"    {name}:")
            print(f"        cropBoxActive: {crop_active}")
            print(f"        cropBoxVisible: {crop_visible}")
    
    # Get crop box info for a specific view
    print("\n[3] Getting detailed crop box info...")
    if 'FRONT EXTERIOR ELEVATION' in view_map:
        view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
        crop_info = send_mcp('getViewCropBox', {'viewId': view_id})
        print(f"    FRONT EXTERIOR ELEVATION crop box:")
        print(f"    {json.dumps(crop_info, indent=4)}")

    # Try enabling crop with cropVisible = True
    print("\n[4] Re-applying crop boxes with visibility enabled...")
    
    # Get building extents for crop calculations
    walls_data = send_mcp('getWalls')
    walls = walls_data.get('walls', [])
    
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = 0, 15  # Default height
    
    for wall in walls:
        for pt in [wall.get('startPoint', {}), wall.get('endPoint', {})]:
            x, y = pt.get('x', 0), pt.get('y', 0)
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
        base = wall.get('baseOffset', 0)
        height = wall.get('height', 10)
        min_z = min(min_z, base)
        max_z = max(max_z, base + height)
    
    width = max_x - min_x
    depth = max_y - min_y
    h_margin = max(width, depth) * 0.15
    
    # Define crop boxes
    elev_views = {
        'FRONT EXTERIOR ELEVATION': [[min_x - h_margin, min_z - 2, -100], [max_x + h_margin, max_z + 5, 100]],
        'REAR EXTERIOR ELEVATION': [[min_x - h_margin, min_z - 2, -100], [max_x + h_margin, max_z + 5, 100]],
        'LEFT-SIDE EXTERIOR ELEVATION': [[min_y - h_margin, min_z - 2, -100], [max_y + h_margin, max_z + 5, 100]],
        'RIGHT-SIDE EXTERIOR ELEVATION': [[min_y - h_margin, min_z - 2, -100], [max_y + h_margin, max_z + 5, 100]],
        'BUILDING SECTION - AA': [[min_x - h_margin, min_z - 2, min_y - h_margin], [max_x + h_margin, max_z + 5, max_y + h_margin]],
    }
    
    for view_name, crop_box in elev_views.items():
        if view_name in view_map:
            view_id = view_map[view_name]['id']
            
            # Try with cropVisible parameter
            result = send_mcp('setViewCropBox', {
                'viewId': view_id,
                'enableCrop': True,
                'cropVisible': True,
                'cropBox': crop_box
            })
            
            if result.get('success'):
                print(f"    {view_name}: Crop applied successfully")
            else:
                print(f"    {view_name}: ERROR - {result.get('error')}")
            
            time.sleep(0.3)
        else:
            print(f"    {view_name}: NOT FOUND")

    print("\n[5] Verifying crop status after fix...")
    views_data = send_mcp('getViews')
    views = views_data.get('result', {}).get('views', [])
    view_map = {v['name']: v for v in views}
    
    for name in test_views[:5]:  # Just check elevations/sections
        if name in view_map:
            v = view_map[name]
            print(f"    {name}: active={v.get('cropBoxActive')}, visible={v.get('cropBoxVisible')}")


if __name__ == '__main__':
    main()
