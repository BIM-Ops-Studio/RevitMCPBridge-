$pipeName = 'RevitMCPBridge2026'

function Send-MCPRequest($request) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()
    return $response | ConvertFrom-Json
}

$views = @(
    @{id=2136700; name="Garage Roof"},
    @{id=2145981; name="Parapet"},
    @{id=2145960; name="Balcony"},
    @{id=2136787; name="Bedroom Balcony"},
    @{id=2136771; name="Canopy"}
)

foreach ($view in $views) {
    Write-Host "`n=== $($view.name) ==="

    # Get all curve elements (lines)
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Lines", "viewId": ' + $view.id + '}}')
    if ($result.success -and $result.result.elements) {
        Write-Host "Lines: $($result.result.count)"
        # Get bounding box to understand view extents
        if ($result.result.elements.Count -gt 0) {
            $firstLine = $result.result.elements[0]
            Write-Host "  First line ID: $($firstLine.id)"
        }
    }

    # Get view crop box to understand coordinate system
    $result = Send-MCPRequest('{"method": "getElementProperties", "params": {"elementId": ' + $view.id + '}}')
    if ($result.success) {
        $props = $result.result.Parameters
        if ($props.'Crop Region Visible') {
            Write-Host "  Crop visible: $($props.'Crop Region Visible'.value)"
        }
    }

    # Get bounding box of view
    $result = Send-MCPRequest('{"method": "getBoundingBox", "params": {"elementId": ' + $view.id + '}}')
    if ($result.success -and $result.result) {
        $bb = $result.result
        Write-Host "  View bounds: X[$($bb.min.x) to $($bb.max.x)], Y[$($bb.min.y) to $($bb.max.y)]"
        Write-Host "  Width: $([math]::Round($bb.max.x - $bb.min.x, 2))ft, Height: $([math]::Round($bb.max.y - $bb.min.y, 2))ft"
    }
}
