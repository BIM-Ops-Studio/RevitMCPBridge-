#!/usr/bin/env python3
"""Test the updated crop box setting and see actual values."""

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
print("TESTING CROP BOX FIX")
print("=" * 70)

# Test connection
print("\n[1] Testing connection...")
levels = send_mcp('getLevels')
if levels.get('success'):
    print(f"    Connected!")
else:
    print(f"    ERROR: {levels.get('error')}")
    exit(1)

# Get FRONT EXTERIOR ELEVATION
views = send_mcp('getViews').get('result', {}).get('views', [])
view_map = {v['name']: v for v in views}
view_id = view_map['FRONT EXTERIOR ELEVATION']['id']

# Get current crop box
print("\n[2] Current crop box:")
current = send_mcp('getViewCropBox', {'viewId': view_id})
crop = current['cropBox']
print(f"    Min: ({crop['min']['x']:.1f}, {crop['min']['y']:.1f}, {crop['min']['z']:.1f})")
print(f"    Max: ({crop['max']['x']:.1f}, {crop['max']['y']:.1f}, {crop['max']['z']:.1f})")
print(f"    Size: {crop['max']['x'] - crop['min']['x']:.0f}' x {crop['max']['y'] - crop['min']['y']:.0f}'")

# Try setting a small test crop box
print("\n[3] Setting test crop box (30' x 20')...")
test_crop = [
    [-15, -5, crop['min']['z']],  # Keep same Z range
    [15, 15, crop['max']['z']]
]
result = send_mcp('setViewCropBox', {
    'viewId': view_id,
    'enableCrop': True,
    'cropBox': test_crop
})

print(f"    Success: {result.get('success')}")
if 'actualCropBox' in result:
    actual = result['actualCropBox']
    print(f"    Actual Min: ({actual['min']['x']:.1f}, {actual['min']['y']:.1f}, {actual['min']['z']:.1f})")
    print(f"    Actual Max: ({actual['max']['x']:.1f}, {actual['max']['y']:.1f}, {actual['max']['z']:.1f})")
    print(f"    Actual Size: {actual['max']['x'] - actual['min']['x']:.0f}' x {actual['max']['y'] - actual['min']['y']:.0f}'")
else:
    print(f"    Result: {json.dumps(result, indent=2)}")

# Verify by querying again
print("\n[4] Verifying crop box after setting:")
verify = send_mcp('getViewCropBox', {'viewId': view_id})
crop = verify['cropBox']
print(f"    Min: ({crop['min']['x']:.1f}, {crop['min']['y']:.1f}, {crop['min']['z']:.1f})")
print(f"    Max: ({crop['max']['x']:.1f}, {crop['max']['y']:.1f}, {crop['max']['z']:.1f})")
print(f"    Size: {crop['max']['x'] - crop['min']['x']:.0f}' x {crop['max']['y'] - crop['min']['y']:.0f}'")
