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

$views = @(
    @{id=2136700; name="Garage Roof"},
    @{id=2145981; name="Parapet"},
    @{id=2145960; name="Balcony"},
    @{id=2136787; name="Bedroom Balcony"},
    @{id=2136771; name="Canopy"}
)

$totalLines = 0
$totalBreaks = 0

Write-Host "=== Adding Detail Lines (Leaders) ==="

foreach ($view in $views) {
    Write-Host "`n$($view.name):"

    # Try createDetailLineVA with individual X,Y,Z params
    $request = '{"method": "createDetailLineVA", "params": {"viewId": ' + $view.id + ', "startX": -0.3, "startY": 0.5, "startZ": 0, "endX": -0.1, "endY": 0.4, "endZ": 0}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        $totalLines++
        Write-Host "  Leader 1 added"
    } else {
        Write-Host "  Failed: $($result.error)"
    }

    # Add another leader
    $request = '{"method": "createDetailLineVA", "params": {"viewId": ' + $view.id + ', "startX": -0.4, "startY": 0.3, "startZ": 0, "endX": -0.2, "endY": 0.2, "endZ": 0}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        $totalLines++
        Write-Host "  Leader 2 added"
    }
}

Write-Host "`n=== Trying Break Lines ==="

foreach ($view in $views) {
    # Try createBreakLine
    $request = '{"method": "createBreakLine", "params": {"viewId": ' + $view.id + ', "startX": -0.2, "startY": -0.5, "endX": 0.2, "endY": -0.5}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success) {
        $totalBreaks++
        Write-Host "  Break line added to $($view.name)"
    } else {
        Write-Host "  Break line failed in $($view.name): $($result.error)"
    }
}

Write-Host "`n=== Trying Insulation ==="

# Try addInsulation to Garage Roof
$request = '{"method": "addInsulation", "params": {"viewId": 2136700}}'
$result = Send-MCPRequest($request)
Write-Host "Insulation result: $result"

Write-Host "`n=== Summary ==="
Write-Host "Detail lines added: $totalLines"
Write-Host "Break lines added: $totalBreaks"
