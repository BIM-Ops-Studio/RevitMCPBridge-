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

# Zoom to fit
result = send_mcp('zoomToFit')
print(f"ZoomToFit: {json.dumps(result)}")
