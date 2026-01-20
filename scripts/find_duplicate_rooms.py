#!/usr/bin/env python3
"""Find duplicate room numbers in the current Revit project."""
import json
import subprocess
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
            # Clean control characters
            line = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line)
            try:
                return json.loads(line)
            except:
                continue
    return {"error": "No JSON found"}


if __name__ == "__main__":
    print("Fetching rooms...")
    result = call_mcp("getRooms")

    if not result.get("success"):
        print(f"Error: {result.get('error')}")
        exit(1)

    rooms = result.get("rooms", [])
    print(f"Total rooms: {len(rooms)}")

    # Find duplicates
    numbers = {}
    for r in rooms:
        num = r.get("number", "")
        if num not in numbers:
            numbers[num] = []
        numbers[num].append(r)

    print("\nDuplicate room numbers:")
    print("=" * 50)

    duplicates = []
    for num, room_list in sorted(numbers.items()):
        if len(room_list) > 1:
            print(f"\n{num}: ({len(room_list)} rooms)")
            for r in room_list:
                print(f"  ID:{r['roomId']} - {r['name']} @ {r['level']}")
                duplicates.append((num, r))

    print(f"\n{'=' * 50}")
    print(f"Found {len(duplicates)} rooms with duplicate numbers")

    # Save to file
    with open("duplicate_rooms.json", "w") as f:
        json.dump([{"number": d[0], **d[1]} for d in duplicates], f, indent=2)
    print("Saved to duplicate_rooms.json")
