#!/usr/bin/env python3
"""Test with a very small crop box to see if it changes the view."""

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
    return json.loads(output) if output else {}

# Get FRONT EXTERIOR ELEVATION view ID
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}

view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
print(f"Testing on FRONT EXTERIOR ELEVATION (ID: {view_id})")

# Try VERY small crop box - should make the view zoom way in
# Testing with just 10' x 10' centered on origin
print("\nSetting a 10' x 10' crop box centered on origin...")
result = send_mcp('setViewCropBox', {
    'viewId': view_id,
    'enableCrop': True,
    'cropBox': [[-5, -5, -5], [5, 5, 5]]
})
print(f"Result: {json.dumps(result, indent=2)}")

print("\nZooming to fit...")
send_mcp('zoomToFit')
print("Done - check Revit to see if the view changed")
