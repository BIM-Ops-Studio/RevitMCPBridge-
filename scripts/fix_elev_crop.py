#!/usr/bin/env python3
"""
Fix elevation crop boxes - use view-relative coordinates.
For elevation views, the crop box is in the view's local coordinate system:
- X = horizontal extent (left-right in view)  
- Y = vertical extent (bottom-top in view, which is Z in world)
- Z = depth extent (near-far clipping)
"""

import subprocess, json, time

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
    result = subprocess.run(['powershell.exe', '-Command', ps_script], capture_output=True, text=True, timeout=30)
    output = result.stdout.strip()
    json_start = output.find('{')
    if json_start >= 0:
        output = output[json_start:]
    try:
        return json.loads(output)
    except:
        return {"success": False, "error": output}

print("=" * 60)
print("FIXING ELEVATION CROP BOXES")
print("=" * 60)

# Get building extents
walls = send_mcp('getWalls').get('walls', [])
min_x, max_x = float('inf'), float('-inf')
min_y, max_y = float('inf'), float('-inf')
min_z, max_z = 0, 15

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
height = max_z - min_z
center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2

print(f"Building: {width:.0f}' x {depth:.0f}' x {height:.0f}'")
print(f"Center: ({center_x:.1f}, {center_y:.1f})")
print(f"Z range: {min_z:.1f} to {max_z:.1f}")

# Margins
h_margin = 5   # 5' horizontal margin
v_margin = 3   # 3' vertical margin
depth_margin = 10  # depth clipping

# Get views
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}

# For elevation views, try different coordinate arrangement
# The crop box for an elevation uses view-local coordinates
# We need to set it relative to the view's origin and orientation

elevations = [
    ('FRONT EXTERIOR ELEVATION', width, height),
    ('REAR EXTERIOR ELEVATION', width, height),
    ('LEFT-SIDE EXTERIOR ELEVATION', depth, height),
    ('RIGHT-SIDE EXTERIOR ELEVATION', depth, height),
]

print("\nSetting crop boxes centered on building:")

for view_name, view_width, view_height in elevations:
    if view_name in view_map:
        view_id = view_map[view_name]['id']
        
        # For elevations, set crop box relative to view center
        # Use symmetric bounds around zero (view center)
        half_w = (view_width / 2) + h_margin
        half_h = (view_height / 2) + v_margin
        
        # Try: X = horizontal, Y = depth, Z = vertical (view coordinates)
        crop_box = [
            [-half_w, -depth_margin, min_z - v_margin],  # Min: left, near, bottom
            [half_w, depth_margin, max_z + v_margin]     # Max: right, far, top
        ]
        
        print(f"\n  {view_name}:")
        print(f"    Crop: X=[{-half_w:.1f}, {half_w:.1f}], Y=[{-depth_margin}, {depth_margin}], Z=[{min_z - v_margin:.1f}, {max_z + v_margin:.1f}]")
        
        result = send_mcp('setViewCropBox', {
            'viewId': view_id,
            'enableCrop': True,
            'cropBox': crop_box
        })
        
        if result.get('success'):
            print(f"    Result: SUCCESS")
        else:
            print(f"    Result: ERROR - {result.get('error')}")
        
        time.sleep(0.3)

# Also do the section
if 'BUILDING SECTION - AA' in view_map:
    view_id = view_map['BUILDING SECTION - AA']['id']
    half_w = (width / 2) + h_margin
    
    crop_box = [
        [-half_w, -depth_margin, min_z - v_margin],
        [half_w, depth_margin, max_z + v_margin]
    ]
    
    print(f"\n  BUILDING SECTION - AA:")
    result = send_mcp('setViewCropBox', {
        'viewId': view_id,
        'enableCrop': True,
        'cropBox': crop_box
    })
    print(f"    Result: {'SUCCESS' if result.get('success') else 'ERROR - ' + result.get('error', '')}")

print("\n" + "=" * 60)
print("Done - check Revit to see if crop boxes are properly sized")
print("=" * 60)
