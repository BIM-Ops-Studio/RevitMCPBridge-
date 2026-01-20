#!/usr/bin/env python3
"""Quick MCP test script"""
import json
import subprocess
import sys

def call_mcp(method: str, params: dict = None):
    """Call MCP method via named pipe."""
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    })

    ps_script = f'''
$pipeName = "RevitMCPBridge2026"
$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {{
    $pipeClient.Connect(10000)
    $writer = New-Object System.IO.StreamWriter($pipeClient)
    $reader = New-Object System.IO.StreamReader($pipeClient)
    $message = '{request.replace("'", "''")}'
    $writer.WriteLine($message)
    $writer.Flush()
    $response = $reader.ReadLine()
    Write-Output $response
}} finally {{
    $pipeClient.Close()
}}
'''
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True, timeout=30
    )
    # Extract JSON from output (skip profile lines)
    output = result.stdout.strip()
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                return json.loads(line)
            except:
                continue
    print(f"Raw output: {output[:500]}")
    return {"error": result.stderr or "No JSON found in output"}


if __name__ == "__main__":
    method = sys.argv[1] if len(sys.argv) > 1 else "getLevels"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    print(f"Calling {method}...")
    result = call_mcp(method, params)
    print(json.dumps(result, indent=2)[:2000])
