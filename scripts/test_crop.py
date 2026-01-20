#!/usr/bin/env python3
"""Direct test of crop box setting."""

import subprocess
import json

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

# Get views
views = send_mcp('getViews')
view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}

# Test on FRONT EXTERIOR ELEVATION
if 'FRONT EXTERIOR ELEVATION' in view_map:
    view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
    print(f"Testing FRONT EXTERIOR ELEVATION (ID: {view_id})")
    
    # First, just enable crop without setting a box
    print("\n1. Enable crop only:")
    result = send_mcp('setViewCropBox', {
        'viewId': view_id,
        'enableCrop': True
    })
    print(f"   Result: {json.dumps(result, indent=4)}")
    
    # Now set a specific crop box
    print("\n2. Set crop box:")
    # For elevation views, the crop box is in the view's coordinate system
    # Min = lower-left corner, Max = upper-right corner
    # Using simple coordinates: -40 to 40 horizontal, -5 to 20 vertical
    result = send_mcp('setViewCropBox', {
        'viewId': view_id,
        'enableCrop': True,
        'cropBox': [[-40, -5, -100], [40, 20, 100]]
    })
    print(f"   Result: {json.dumps(result, indent=4)}")

# Also test on FLOOR PLAN
if 'FLOOR PLAN' in view_map:
    view_id = view_map['FLOOR PLAN']['id']
    print(f"\n\nTesting FLOOR PLAN (ID: {view_id})")
    
    print("\n1. Enable crop and set box:")
    result = send_mcp('setViewCropBox', {
        'viewId': view_id,
        'enableCrop': True,
        'cropBox': [[-35, -30, -10], [40, 35, 50]]
    })
    print(f"   Result: {json.dumps(result, indent=4)}")
