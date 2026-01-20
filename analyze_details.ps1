$pipeName = 'RevitMCPBridge2026'

$views = @(
    @{id=2136700; name="Detail 4 - Garage Roof"},
    @{id=2145981; name="Detail 5 - Parapet"},
    @{id=2145960; name="Detail 1 - Balcony"},
    @{id=2136787; name="Detail 2 - Bedroom Balcony"},
    @{id=2136771; name="Detail 3 - Canopy"}
)

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

$allData = @{}

foreach ($view in $views) {
    Write-Host "`n=============================================="
    Write-Host "=== $($view.name) (ID: $($view.id)) ==="
    Write-Host "=============================================="

    $viewData = @{}

    # Get detail lines
    $result = Send-MCPRequest('{"method": "getDetailLinesInView", "params": {"viewId": ' + $view.id + '}}')
    if ($result.success) {
        $lineCount = $result.result.count
        Write-Host "Detail Lines: $lineCount"
        $viewData["detailLines"] = $lineCount
    }

    # Get dimensions
    $result = Send-MCPRequest('{"method": "getDimensionsInView", "params": {"viewId": ' + $view.id + '}}')
    if ($result.success) {
        $dimCount = $result.result.count
        Write-Host "Dimensions: $dimCount"
        $viewData["dimensions"] = $dimCount
        if ($result.result.dimensions) {
            foreach ($dim in $result.result.dimensions) {
                Write-Host "  - $($dim.value)"
            }
        }
    }

    # Get text notes
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Text Notes", "viewId": ' + $view.id + '}}')
    if ($result.success) {
        $textCount = $result.result.count
        Write-Host "Text Notes: $textCount"
        $viewData["textNotes"] = $textCount
    }

    # Get detail components
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Detail Items", "viewId": ' + $view.id + '}}')
    if ($result.success) {
        $compCount = $result.result.count
        Write-Host "Detail Components: $compCount"
        $viewData["detailComponents"] = $compCount
        if ($result.result.elements) {
            $types = $result.result.elements | Group-Object -Property name
            foreach ($t in $types) {
                Write-Host "  - $($t.Name): $($t.Count)"
            }
        }
    }

    # Get filled regions
    $result = Send-MCPRequest('{"method": "getElements", "params": {"category": "Filled region", "viewId": ' + $view.id + '}}')
    if ($result.success -and $result.result.elements) {
        $fillCount = $result.result.count
        Write-Host "Filled Regions: $fillCount"
        $viewData["filledRegions"] = $fillCount
    }

    # Get annotations
    $result = Send-MCPRequest('{"method": "getAllAnnotationsInView", "params": {"viewId": ' + $view.id + '}}')
    if ($result.success) {
        Write-Host "Total Annotations: $($result.result.totalCount)"
    }

    $allData[$view.name] = $viewData
}

Write-Host "`n`n=== SUMMARY ==="
foreach ($key in $allData.Keys) {
    $d = $allData[$key]
    Write-Host "$key"
    Write-Host "  Lines: $($d.detailLines), Dims: $($d.dimensions), Text: $($d.textNotes), Components: $($d.detailComponents)"
}
