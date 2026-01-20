#!/usr/bin/env python3
"""Simple MCP client for RevitMCPBridge"""
import subprocess
import json
import sys

def send_command(command, params=None):
    request = json.dumps({'command': command, 'params': params or {}}, ensure_ascii=False)
    # Escape for PowerShell
    request_escaped = request.replace('"', '\\"')

    ps_script = f'''
$ErrorActionPreference = "Stop"
try {{
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCP", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.WriteLine("{request_escaped}")
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    $response
}} catch {{
    Write-Error $_.Exception.Message
}}
'''

    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps_script],
        capture_output=True,
        text=True,
        timeout=60
    )

    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        return {'error': result.stderr or 'No response', 'stdout': output}

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {'raw': output[:3000]}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python revit_mcp_client.py <command> [params_json]")
        sys.exit(1)

    cmd = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    result = send_command(cmd, params)
    print(json.dumps(result, indent=2, ensure_ascii=False))
