#!/usr/bin/env python3
"""Set a room number using MCP."""
import json
import subprocess
import sys
import re

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
        capture_output=True, text=True, timeout=60
    )

    # Extract JSON from output
    output = result.stdout.strip()
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            line = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line)
            try:
                return json.loads(line)
            except:
                continue
    return {"error": "No JSON found", "raw": output[:500]}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python set_room_number.py <room_id> <new_number>")
        print("Example: python set_room_number.py 4933336 S01")
        sys.exit(1)

    room_id = int(sys.argv[1])
    new_number = sys.argv[2]

    print(f"Setting room {room_id} number to '{new_number}'...")

    result = call_mcp("setRoomNumber", {"roomId": room_id, "number": new_number})

    if result.get("success"):
        print(f"SUCCESS!")
        print(f"  Room ID: {result.get('roomId')}")
        print(f"  Old number: {result.get('oldNumber')}")
        print(f"  New number: {result.get('newNumber')}")
        print(f"  Name: {result.get('name')}")
    else:
        print(f"FAILED: {result.get('error')}")
        print(json.dumps(result, indent=2))
