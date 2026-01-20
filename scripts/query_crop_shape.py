#!/usr/bin/env python3
"""Query the existing crop shape to understand the coordinate system."""

import subprocess, json

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

# Get view info
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}

print("FRONT EXTERIOR ELEVATION crop box details:")
view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
result = send_mcp('getViewCropBox', {'viewId': view_id})

if result.get('success'):
    crop = result['cropBox']
    transform = result['transform']
    
    print(f"\nCrop Box (view coordinates):")
    print(f"  Min: ({crop['min']['x']:.2f}, {crop['min']['y']:.2f}, {crop['min']['z']:.2f})")
    print(f"  Max: ({crop['max']['x']:.2f}, {crop['max']['y']:.2f}, {crop['max']['z']:.2f})")
    print(f"  Size: {crop['max']['x'] - crop['min']['x']:.0f}' x {crop['max']['y'] - crop['min']['y']:.0f}'")
    
    print(f"\nTransform:")
    print(f"  Origin: ({transform['origin']['x']:.2f}, {transform['origin']['y']:.2f}, {transform['origin']['z']:.2f})")
    print(f"  BasisX: ({transform['basisX']['x']:.2f}, {transform['basisX']['y']:.2f}, {transform['basisX']['z']:.2f})")
    print(f"  BasisY: ({transform['basisY']['x']:.2f}, {transform['basisY']['y']:.2f}, {transform['basisY']['z']:.2f})")
    print(f"  BasisZ: ({transform['basisZ']['x']:.2f}, {transform['basisZ']['y']:.2f}, {transform['basisZ']['z']:.2f})")

# Also check FLOOR PLAN for comparison
print("\n" + "="*50)
print("FLOOR PLAN crop box for comparison:")
view_id = view_map['FLOOR PLAN']['id']
result = send_mcp('getViewCropBox', {'viewId': view_id})

if result.get('success'):
    crop = result['cropBox']
    transform = result['transform']
    
    print(f"\nCrop Box (view coordinates):")
    print(f"  Min: ({crop['min']['x']:.2f}, {crop['min']['y']:.2f}, {crop['min']['z']:.2f})")
    print(f"  Max: ({crop['max']['x']:.2f}, {crop['max']['y']:.2f}, {crop['max']['z']:.2f})")
    print(f"  Size: {crop['max']['x'] - crop['min']['x']:.0f}' x {crop['max']['y'] - crop['min']['y']:.0f}'")
