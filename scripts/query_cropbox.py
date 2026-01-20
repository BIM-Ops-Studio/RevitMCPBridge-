#!/usr/bin/env python3
"""Query crop box coordinates to understand the coordinate system."""

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
print("QUERYING CROP BOX COORDINATES")
print("=" * 70)

# Test connection
print("\n[1] Testing connection...")
levels = send_mcp('getLevels')
if levels.get('success'):
    print(f"    Connected! Found {levels.get('levelCount')} levels")
else:
    print(f"    ERROR: {levels.get('error')}")
    exit(1)

# Get views
print("\n[2] Getting views...")
views = send_mcp('getViews')
views_list = views.get('result', {}).get('views', [])
view_map = {v['name']: v for v in views_list}
print(f"    Found {len(views_list)} views")

# Query crop box for FRONT EXTERIOR ELEVATION
print("\n[3] Querying FRONT EXTERIOR ELEVATION crop box...")
if 'FRONT EXTERIOR ELEVATION' in view_map:
    view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
    result = send_mcp('getViewCropBox', {'viewId': view_id})
    print(json.dumps(result, indent=2))
else:
    print("    View not found!")

# Also query a floor plan for comparison
print("\n[4] Querying FLOOR PLAN crop box for comparison...")
if 'FLOOR PLAN' in view_map:
    view_id = view_map['FLOOR PLAN']['id']
    result = send_mcp('getViewCropBox', {'viewId': view_id})
    print(json.dumps(result, indent=2))
