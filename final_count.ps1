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
    @{id=2136700; name="Detail 4 - Garage Roof"},
    @{id=2145981; name="Detail 5 - Parapet"},
    @{id=2145960; name="Detail 1 - Balcony"},
    @{id=2136787; name="Detail 2 - Bedroom Balcony"},
    @{id=2136771; name="Detail 3 - Canopy"}
)

Write-Host "======================================"
Write-Host "FINAL COUNT - Sheet A9.2 Typical Details"
Write-Host "======================================"

$totalText = 0
$totalDims = 0
$totalComponents = 0

foreach ($view in $views) {
    Write-Host "`n$($view.name):"

    # Count text notes
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Text Notes", "viewId": ' + $view.id + '}}') | ConvertFrom-Json
    if ($result.success) {
        $count = $result.result.count
        Write-Host "  Text Notes: $count"
        $totalText += $count
    }

    # Count dimensions
    $result = Send-MCPRequest('{"method": "getDimensionsInView", "params": {"viewId": ' + $view.id + '}}') | ConvertFrom-Json
    if ($result.success) {
        $count = $result.result.count
        Write-Host "  Dimensions: $count"
        $totalDims += $count
    }

    # Count detail components
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Detail Items", "viewId": ' + $view.id + '}}') | ConvertFrom-Json
    if ($result.success) {
        $count = $result.result.count
        Write-Host "  Detail Components: $count"
        $totalComponents += $count
    }
}

Write-Host "`n======================================"
Write-Host "TOTALS ACROSS ALL 5 DETAILS:"
Write-Host "  Text Notes: $totalText"
Write-Host "  Dimensions: $totalDims"
Write-Host "  Detail Components: $totalComponents"
Write-Host "======================================"
