$pipeName = 'RevitMCPBridge2026'

function Send-MCPRequest($request) {
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $response = $reader.ReadLine()
        $pipe.Close()
        return $response
    } catch {
        Write-Host "Error: $_"
        return $null
    }
}

Write-Host "=== Getting Break Line family info ==="

# Get the break line family type ID
$result = Send-MCPRequest('{"method": "getFamilyInstanceTypes", "params": {"category": "Detail Items"}}')
Write-Host "Detail Item types sample: "
$parsed = $result | ConvertFrom-Json
if ($parsed.success) {
    $breakLines = $parsed.result.familyTypes | Where-Object { $_.familyName -like "*Break*" }
    Write-Host "Break Line types found:"
    foreach ($bl in $breakLines) {
        Write-Host "  Family: $($bl.familyName), Type: $($bl.typeName), ID: $($bl.typeId)"
    }
}

Write-Host "`n=== Trying to place detail component ==="

# Try placing a break line using placeDetailComponent
$request = '{"method": "placeDetailComponent", "params": {"viewId": 2136700, "familyName": "Break Line", "typeName": "Break Line", "location": [0, 0.5, 0]}}'
$result = Send-MCPRequest($request)
Write-Host "Place result: $result"

Write-Host "`n=== Trying createDetailLine ==="

# Try creating detail lines (for leaders)
$request = '{"method": "createDetailLine", "params": {"viewId": 2136700, "start": [0.5, 0.5, 0], "end": [0.8, 0.7, 0]}}'
$result = Send-MCPRequest($request)
Write-Host "Detail line result: $result"

# Try another line
$request = '{"method": "createDetailLine", "params": {"viewId": 2136700, "start": [0.5, 0.3, 0], "end": [0.8, 0.4, 0]}}'
$result = Send-MCPRequest($request)
Write-Host "Detail line 2 result: $result"
