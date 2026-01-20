#!/usr/bin/env python3
"""Test which crop method is being used and what values are returned."""

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

print("=" * 70)
print("TESTING CROP BOX METHOD")
print("=" * 70)

# Get views
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}

view_id = view_map['FRONT EXTERIOR ELEVATION']['id']

# Try setting a small test crop box and see full response
print("\n[1] Setting test crop box on FRONT EXTERIOR ELEVATION...")
test_crop = [
    [-20, -5, -100],
    [20, 20, 100]
]
result = send_mcp('setViewCropBox', {
    'viewId': view_id,
    'enableCrop': True,
    'cropBox': test_crop
})

print(json.dumps(result, indent=2))

print("\n[2] Query crop box to verify:")
verify = send_mcp('getViewCropBox', {'viewId': view_id})
crop = verify['cropBox']
width = crop['max']['x'] - crop['min']['x']
height = crop['max']['y'] - crop['min']['y']
print(f"    Size: {width:.0f}' x {height:.0f}'")
