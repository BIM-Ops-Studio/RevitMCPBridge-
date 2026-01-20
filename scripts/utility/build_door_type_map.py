#!/usr/bin/env python3
"""Build door type mapping and generate placement script"""
import json
import socket

def send_mcp_request(request):
    """Send request to MCP server via named pipe"""
    import subprocess

    ps_script = f'''
$pipeName = 'RevitMCPBridge2026'
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipe)
$reader = New-Object System.IO.StreamReader($pipe)
$writer.AutoFlush = $true
$request = '{json.dumps(request)}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()
Write-Output $response
'''

    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-Command', ps_script],
        capture_output=True, text=True
    )

    # Find JSON in output
    for line in result.stdout.split('\n'):
        if line.strip().startswith('{'):
            return json.loads(line)
    return None

# Family ID mapping (from getLoadedFamilies result)
FAMILY_MAP = {
    "Door-Bifold_4-Panel_Flush_SlimFold_Dunbarton": 1240517,
    "Door-Double-Sliding": 1241534,
    "Door-Exterior-Single-Entry-Half Flat Glass-Wood_Clad": 1242607,
    "Door-Garage-Embossed_Panel": 1246434,
    "Door-Interior-Double-Sliding-2_Panel-Wood": 1249236,
    "Door-Interior-Single-Flush_Panel-Wood": 1251110,
    "Door-Interior-Single-Pocket-2_Panel-Wood": 1254116,
    "Door-Opening": 1255579,
    "Door-Passage-Single-Flush": 1256468,  # Transferred one
}

# Also check the pre-existing one
PRE_EXISTING_FAMILIES = {
    "Door-Passage-Single-Flush": 634676,
}

print("Building door type mapping...")

# Get all types for each family
type_map = {}  # {familyName: {typeName: typeId}}

for family_name, family_id in FAMILY_MAP.items():
    print(f"  Getting types for {family_name}...")

    response = send_mcp_request({
        "method": "getFamilyTypes",
        "params": {"familyId": family_id}
    })

    if response and response.get("success"):
        types = response.get("types", [])
        type_map[family_name] = {t["typeName"]: t["typeId"] for t in types}
        print(f"    Found {len(types)} types")
    else:
        print(f"    ERROR: {response.get('error') if response else 'No response'}")

# Also get pre-existing Door-Passage-Single-Flush
print("  Getting types for pre-existing Door-Passage-Single-Flush...")
response = send_mcp_request({
    "method": "getFamilyTypes",
    "params": {"familyId": 634676}
})
if response and response.get("success"):
    types = response.get("types", [])
    if "Door-Passage-Single-Flush" not in type_map:
        type_map["Door-Passage-Single-Flush"] = {}
    for t in types:
        type_map["Door-Passage-Single-Flush"][t["typeName"]] = t["typeId"]
    print(f"    Found {len(types)} types (pre-existing)")

# Load door data
print("\nLoading door data...")
with open("/mnt/d/RevitMCPBridge2026/avon_park_doors_windows.json", "r", encoding="utf-8-sig") as f:
    door_data = json.load(f)

doors = door_data.get("doors", [])
print(f"Found {len(doors)} doors to place")

# Build placement data with type IDs
placement_data = []
missing_types = []

for i, door in enumerate(doors):
    family_name = door.get("familyName")
    type_name = door.get("typeName")
    location = door.get("location")

    # Find type ID
    type_id = None
    if family_name in type_map:
        type_id = type_map[family_name].get(type_name)

    if type_id:
        placement_data.append({
            "index": i + 1,
            "familyName": family_name,
            "typeName": type_name,
            "typeId": type_id,
            "location": location
        })
    else:
        missing_types.append(f"Door {i+1}: {family_name} - {type_name}")

print(f"\nMatched {len(placement_data)} doors")
if missing_types:
    print(f"Missing {len(missing_types)} type mappings:")
    for m in missing_types:
        print(f"  {m}")

# Save placement data
output_file = "/mnt/d/RevitMCPBridge2026/door_placement_data.json"
with open(output_file, "w") as f:
    json.dump(placement_data, f, indent=2)
print(f"\nSaved placement data to {output_file}")

# Generate PowerShell placement script
ps_script = '''# Place doors with type IDs
$pipeName = 'RevitMCPBridge2026'

$placementData = Get-Content "D:\\RevitMCPBridge2026\\door_placement_data.json" -Raw | ConvertFrom-Json

Write-Host "Placing $($placementData.Count) doors..."
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($door in $placementData) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $x = $door.location[0]
    $y = $door.location[1]
    $z = $door.location[2]

    $request = @{
        method = "placeFamilyInstance"
        params = @{
            familyTypeId = $door.typeId
            location = @($x, $y, $z)
            levelId = 30
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $result = $response | ConvertFrom-Json
    if ($result.success) {
        $successCount++
        Write-Host "Placed door $($door.index): $($door.familyName) - $($door.typeName)"
    } else {
        $failCount++
        Write-Host "FAILED door $($door.index): $($result.error)"
    }

    Start-Sleep -Milliseconds 200
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Door placement complete!"
Write-Host "Success: $successCount"
Write-Host "Failed: $failCount"
Write-Host "=========================================="
'''

ps_file = "/mnt/d/RevitMCPBridge2026/place_doors_with_ids.ps1"
with open(ps_file, "w") as f:
    f.write(ps_script)
print(f"Generated placement script: {ps_file}")
