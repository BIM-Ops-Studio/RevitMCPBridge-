#!/usr/bin/env python3
"""Enable crop region on views without changing the crop box size."""

import subprocess
import json
import time

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

print("=" * 60)
print("ENABLING CROP REGIONS ON ALL VIEWS")
print("=" * 60)

# Get all views
views_data = send_mcp('getViews')
views = views_data.get('result', {}).get('views', [])

# Views to crop
target_views = [
    'FRONT EXTERIOR ELEVATION',
    'REAR EXTERIOR ELEVATION',
    'LEFT-SIDE EXTERIOR ELEVATION',
    'RIGHT-SIDE EXTERIOR ELEVATION',
    'BUILDING SECTION - AA',
    'FLOOR PLAN',
    'ROOF PLAN',
    'COLUMN PLAN',
    'SITE PLAN',
    'MECHANICAL PLAN',
    'ELECTRICAL POWER PLAN',
    'ELECTRICAL LIGHTING PLAN',
    'PLUMBING PLAN'
]

view_map = {v['name']: v for v in views}

print("\nEnabling crop (keeping existing crop box size):\n")

for view_name in target_views:
    if view_name in view_map:
        view_id = view_map[view_name]['id']
        
        # Just enable crop - don't set crop box coordinates
        result = send_mcp('setViewCropBox', {
            'viewId': view_id,
            'enableCrop': True
        })
        
        if result.get('success'):
            active = result.get('cropBoxActive', False)
            print(f"  {view_name}: cropBoxActive = {active}")
        else:
            print(f"  {view_name}: ERROR - {result.get('error')}")
        
        time.sleep(0.2)
    else:
        print(f"  {view_name}: NOT FOUND")

print("\n" + "=" * 60)
print("Done! Check Revit to see if crop regions are now enabled.")
print("If they are, we can then adjust the crop box sizes.")
print("=" * 60)
