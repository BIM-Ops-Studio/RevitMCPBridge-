#!/usr/bin/env python3
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

# Get views and find elevation
views = send_mcp('getViews')
view_map = {v['name']: v for v in views.get('result', {}).get('views', [])}

if 'FRONT EXTERIOR ELEVATION' in view_map:
    view_id = view_map['FRONT EXTERIOR ELEVATION']['id']
    print(f"Opening FRONT EXTERIOR ELEVATION (ID: {view_id})")
    
    # Set as active view
    result = send_mcp('setActiveView', {'viewId': view_id})
    print(f"setActiveView result: {json.dumps(result)}")
