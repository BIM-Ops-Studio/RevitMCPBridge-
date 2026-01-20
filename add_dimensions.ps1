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

$totalDims = 0

foreach ($view in $views) {
    Write-Host "`n=== $($view.name) ==="

    # Try horizontal dimensions only
    $request = '{"method": "batchDimensionWalls", "params": {"viewId": ' + $view.id + ', "direction": "horizontal", "offset": 2.0}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success -and $result.dimensionStringsCreated -gt 0) {
        Write-Host "  Horizontal: $($result.dimensionStringsCreated) dimension(s)"
        $totalDims += $result.dimensionStringsCreated
    }

    # Try vertical dimensions only
    $request = '{"method": "batchDimensionWalls", "params": {"viewId": ' + $view.id + ', "direction": "vertical", "offset": 2.0}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success -and $result.dimensionStringsCreated -gt 0) {
        Write-Host "  Vertical: $($result.dimensionStringsCreated) dimension(s)"
        $totalDims += $result.dimensionStringsCreated
    }

    # Try dimensioning doors
    $request = '{"method": "batchDimensionDoors", "params": {"viewId": ' + $view.id + '}}'
    $result = Send-MCPRequest($request) | ConvertFrom-Json
    if ($result.success -and $result.dimensionsCreated -gt 0) {
        Write-Host "  Doors: $($result.dimensionsCreated) dimension(s)"
        $totalDims += $result.dimensionsCreated
    }
}

Write-Host "`n=== Total dimensions added: $totalDims ==="

# Now let's try creating specific linear dimensions if we can get line references
Write-Host "`n=== Trying createLinearDimension ==="

# Get detail lines from Garage Roof to use as references
$result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Lines", "viewId": 2136700, "limit": 20}}')
Write-Host "Lines result: $result"
