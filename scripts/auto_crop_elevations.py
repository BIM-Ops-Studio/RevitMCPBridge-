#!/usr/bin/env python3
"""
Automatic crop boxes and scales for elevations and sections.
Uses building extents to calculate appropriate crop regions.
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


def get_building_extents(walls):
    """Calculate full 3D bounding box from walls."""
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')
    min_z = float('inf')
    max_z = float('-inf')

    for wall in walls:
        start = wall.get('startPoint', {})
        end = wall.get('endPoint', {})
        
        # Get base and top elevations
        base_offset = wall.get('baseOffset', 0)
        height = wall.get('height', 10)  # Default 10' if not specified
        
        for pt in [start, end]:
            x, y = pt.get('x', 0), pt.get('y', 0)
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
        
        # Track Z extents
        min_z = min(min_z, base_offset)
        max_z = max(max_z, base_offset + height)

    return {
        'min_x': min_x, 'max_x': max_x,
        'min_y': min_y, 'max_y': max_y,
        'min_z': min_z, 'max_z': max_z,
        'width': max_x - min_x,
        'depth': max_y - min_y,
        'height': max_z - min_z,
        'center_x': (min_x + max_x) / 2,
        'center_y': (min_y + max_y) / 2,
        'center_z': (min_z + max_z) / 2
    }


def main():
    print("=" * 70)
    print("AUTOMATIC ELEVATION & SECTION CROPPING")
    print("=" * 70)

    # Step 1: Get walls and calculate building extents
    print("\n[1] Analyzing building geometry...")
    walls_data = send_mcp('getWalls')
    if not walls_data.get('success'):
        print(f"ERROR: Could not get walls: {walls_data.get('error')}")
        return

    walls = walls_data.get('walls', [])
    extents = get_building_extents(walls)

    print(f"    Building extents:")
    print(f"      Width (X):  {extents['width']:.1f} feet")
    print(f"      Depth (Y):  {extents['depth']:.1f} feet")
    print(f"      Height (Z): {extents['height']:.1f} feet")
    print(f"      Z range: {extents['min_z']:.1f} to {extents['max_z']:.1f}")

    # Step 2: Get levels to understand building height better
    print("\n[2] Getting levels...")
    levels_data = send_mcp('getLevels')
    if levels_data.get('success'):
        for level in levels_data.get('levels', []):
            print(f"      {level['name']}: {level['elevation']:.1f}'")

    # Step 3: Get all views
    print("\n[3] Getting views...")
    views_data = send_mcp('getViews')
    if not views_data.get('success'):
        print(f"ERROR: Could not get views: {views_data.get('error')}")
        return

    views = views_data.get('result', {}).get('views', [])
    
    # Create view lookup and categorize
    elevations = []
    sections = []
    
    for v in views:
        name = v.get('name', '').upper()
        view_type = v.get('viewType', '')
        
        if 'ELEVATION' in name or view_type == 'Elevation':
            elevations.append(v)
        elif 'SECTION' in name or view_type == 'Section':
            sections.append(v)

    print(f"    Found {len(elevations)} elevations, {len(sections)} sections")

    # Step 4: Calculate crop regions
    print("\n[4] Calculating crop regions...")
    
    # Elevation crop box - full width/depth plus margins, full height plus margins
    h_margin = max(extents['width'], extents['depth']) * 0.15  # 15% horizontal margin
    v_margin_bottom = 2  # 2' below grade for foundation
    v_margin_top = 5     # 5' above roof for parapet/chimney
    
    # For front/rear elevations (looking along Y axis): use X width
    # For left/right elevations (looking along X axis): use Y depth
    
    front_rear_crop = [
        [extents['min_x'] - h_margin, extents['min_z'] - v_margin_bottom, -1000],
        [extents['max_x'] + h_margin, extents['max_z'] + v_margin_top, 1000]
    ]
    
    left_right_crop = [
        [extents['min_y'] - h_margin, extents['min_z'] - v_margin_bottom, -1000],
        [extents['max_y'] + h_margin, extents['max_z'] + v_margin_top, 1000]
    ]
    
    # Section crop - similar to elevations but cuts through building
    section_crop = [
        [extents['min_x'] - h_margin, extents['min_z'] - v_margin_bottom, extents['min_y'] - h_margin],
        [extents['max_x'] + h_margin, extents['max_z'] + v_margin_top, extents['max_y'] + h_margin]
    ]

    # Generic crop for any view (works for both orientations)
    max_dim = max(extents['width'], extents['depth'])
    generic_elev_crop = [
        [-max_dim/2 - h_margin, extents['min_z'] - v_margin_bottom, -1000],
        [max_dim/2 + h_margin, extents['max_z'] + v_margin_top, 1000]
    ]

    # Step 5: Apply crop boxes and scales
    print("\n[5] Applying crop boxes and scales...")
    
    # Elevations - 1/4" = 1'-0" (scale 48)
    elevation_scale = 48
    for elev in elevations:
        view_id = elev['id']
        view_name = elev['name']
        
        # Determine orientation from name
        name_upper = view_name.upper()
        if 'FRONT' in name_upper or 'REAR' in name_upper or 'BACK' in name_upper:
            crop = front_rear_crop
            crop_desc = f"{extents['width'] + 2*h_margin:.0f}' wide"
        elif 'LEFT' in name_upper or 'RIGHT' in name_upper or 'SIDE' in name_upper:
            crop = left_right_crop
            crop_desc = f"{extents['depth'] + 2*h_margin:.0f}' wide"
        else:
            # Generic - use larger dimension
            crop = [
                [-(max_dim/2 + h_margin), extents['min_z'] - v_margin_bottom, -1000],
                [max_dim/2 + h_margin, extents['max_z'] + v_margin_top, 1000]
            ]
            crop_desc = f"{max_dim + 2*h_margin:.0f}' wide"
        
        # Set scale
        scale_result = send_mcp('setViewScale', {'viewId': view_id, 'scale': elevation_scale})
        if scale_result.get('success'):
            print(f"    {view_name}: Scale set to {elevation_scale} (1/4\" = 1'-0\")")
        else:
            print(f"    {view_name}: Scale ERROR - {scale_result.get('error')}")
        
        time.sleep(0.2)
        
        # Set crop box
        crop_result = send_mcp('setViewCropBox', {
            'viewId': view_id,
            'enableCrop': True,
            'cropBox': crop
        })
        if crop_result.get('success'):
            crop_height = crop[1][1] - crop[0][1]
            print(f"             Crop: {crop_desc} x {crop_height:.0f}' tall")
        else:
            print(f"             Crop ERROR - {crop_result.get('error')}")
        
        time.sleep(0.2)

    # Sections - 1/4" = 1'-0" (scale 48)
    section_scale = 48
    for sect in sections:
        view_id = sect['id']
        view_name = sect['name']
        
        # Set scale
        scale_result = send_mcp('setViewScale', {'viewId': view_id, 'scale': section_scale})
        if scale_result.get('success'):
            print(f"    {view_name}: Scale set to {section_scale} (1/4\" = 1'-0\")")
        else:
            print(f"    {view_name}: Scale ERROR - {scale_result.get('error')}")
        
        time.sleep(0.2)
        
        # Set crop box
        crop_result = send_mcp('setViewCropBox', {
            'viewId': view_id,
            'enableCrop': True,
            'cropBox': section_crop
        })
        if crop_result.get('success'):
            crop_width = section_crop[1][0] - section_crop[0][0]
            crop_height = section_crop[1][1] - section_crop[0][1]
            print(f"             Crop: {crop_width:.0f}' x {crop_height:.0f}'")
        else:
            print(f"             Crop ERROR - {crop_result.get('error')}")
        
        time.sleep(0.2)

    # Step 6: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nBuilding: {extents['width']:.0f}' wide x {extents['depth']:.0f}' deep x {extents['height']:.0f}' tall")
    print(f"\nElevations configured: {len(elevations)}")
    print(f"Sections configured: {len(sections)}")
    print(f"\nAll views set to 1/4\" = 1'-0\" (scale 48)")
    print(f"Crop margins: {h_margin:.0f}' horizontal, {v_margin_bottom}' below grade, {v_margin_top}' above roof")


if __name__ == '__main__':
    main()
