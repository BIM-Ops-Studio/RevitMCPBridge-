#!/usr/bin/env python3
"""Fix elevation crop boxes using correct view coordinates."""

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

print("=" * 70)
print("FIXING ELEVATION CROP BOXES WITH CORRECT COORDINATES")
print("=" * 70)

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

print(f"\nBuilding extents (World):")
print(f"  X: {min_x:.1f} to {max_x:.1f} ({max_x - min_x:.0f}')")
print(f"  Y: {min_y:.1f} to {max_y:.1f} ({max_y - min_y:.0f}')")
print(f"  Z: {min_z:.1f} to {max_z:.1f} ({max_z - min_z:.0f}')")

# Margins
h_margin = 5  # horizontal margin
v_margin = 3  # vertical margin

# Get views
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}

# Process each elevation
elevations = [
    'FRONT EXTERIOR ELEVATION',
    'REAR EXTERIOR ELEVATION',
    'LEFT-SIDE EXTERIOR ELEVATION',
    'RIGHT-SIDE EXTERIOR ELEVATION',
    'BUILDING SECTION - AA'
]

print("\n" + "=" * 70)

for view_name in elevations:
    if view_name not in view_map:
        print(f"\n{view_name}: NOT FOUND")
        continue
    
    view_id = view_map[view_name]['id']
    
    # Get current crop box to understand the transform
    crop_data = send_mcp('getViewCropBox', {'viewId': view_id})
    if not crop_data.get('success'):
        print(f"\n{view_name}: ERROR getting crop box")
        continue
    
    transform = crop_data['transform']
    origin = transform['origin']
    basisX = transform['basisX']
    basisY = transform['basisY']
    basisZ = transform['basisZ']
    current_crop = crop_data['cropBox']
    
    print(f"\n{view_name}:")
    print(f"  Transform origin: ({origin['x']:.1f}, {origin['y']:.1f}, {origin['z']:.1f})")
    
    # Calculate building position in view coordinates
    # For each corner of the building, convert to view coordinates
    # View coords = inverse transform of (world - origin)
    
    # Determine view orientation from basisZ (view direction)
    bz = (basisZ['x'], basisZ['y'], basisZ['z'])
    
    # Calculate view-space bounds for the building
    # We need to find where the building corners map in view space
    
    building_corners = [
        (min_x, min_y, min_z),
        (min_x, min_y, max_z),
        (min_x, max_y, min_z),
        (min_x, max_y, max_z),
        (max_x, min_y, min_z),
        (max_x, min_y, max_z),
        (max_x, max_y, min_z),
        (max_x, max_y, max_z),
    ]
    
    # Transform each corner to view coordinates
    # View = BasisMatrix^-1 * (World - Origin)
    # For orthonormal basis, inverse = transpose
    view_xs, view_ys, view_zs = [], [], []
    
    for wx, wy, wz in building_corners:
        # Translate to origin
        dx = wx - origin['x']
        dy = wy - origin['y']
        dz = wz - origin['z']
        
        # Project onto basis vectors (dot products)
        vx = dx * basisX['x'] + dy * basisX['y'] + dz * basisX['z']
        vy = dx * basisY['x'] + dy * basisY['y'] + dz * basisY['z']
        vz = dx * basisZ['x'] + dy * basisZ['y'] + dz * basisZ['z']
        
        view_xs.append(vx)
        view_ys.append(vy)
        view_zs.append(vz)
    
    # Get bounds in view coordinates
    view_min_x = min(view_xs) - h_margin
    view_max_x = max(view_xs) + h_margin
    view_min_y = min(view_ys) - v_margin  # This is vertical (Z in world for elevations)
    view_max_y = max(view_ys) + v_margin
    view_min_z = min(view_zs) - 10  # Depth margin
    view_max_z = max(view_zs) + 10
    
    print(f"  Building in view coords:")
    print(f"    X (horiz): {min(view_xs):.1f} to {max(view_xs):.1f}")
    print(f"    Y (vert):  {min(view_ys):.1f} to {max(view_ys):.1f}")
    print(f"    Z (depth): {min(view_zs):.1f} to {max(view_zs):.1f}")
    
    # Create new crop box
    new_crop = [
        [view_min_x, view_min_y, view_min_z],
        [view_max_x, view_max_y, view_max_z]
    ]
    
    crop_width = view_max_x - view_min_x
    crop_height = view_max_y - view_min_y
    
    print(f"  New crop: {crop_width:.0f}' x {crop_height:.0f}'")
    
    # Apply new crop box
    result = send_mcp('setViewCropBox', {
        'viewId': view_id,
        'enableCrop': True,
        'cropBox': new_crop
    })
    
    if result.get('success'):
        print(f"  Result: SUCCESS")
    else:
        print(f"  Result: ERROR - {result.get('error')}")
    
    time.sleep(0.3)

print("\n" + "=" * 70)
print("COMPLETE - Elevation crop boxes set to fit building")
print("=" * 70)
