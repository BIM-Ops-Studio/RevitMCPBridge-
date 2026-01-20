# Analyze Office 40 in detail using View Snapshot
function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

Write-Host "`nGetting complete view snapshot..." -ForegroundColor Cyan

$snapshot = Send-RevitCommand -Method "getViewSnapshot" -Params @{
    includeGeometry = $true
    includeParameters = $true
    maxElements = 2000
}

if ($snapshot.success) {
    Write-Host "`nView: $($snapshot.viewInfo.viewName)" -ForegroundColor Green
    Write-Host "Total Elements: $($snapshot.elementCount)" -ForegroundColor White

    Write-Host "`nElements by Category:" -ForegroundColor Cyan
    $snapshot.elementsByCategory.PSObject.Properties | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor Gray
    }

    # Find Office 40
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "OFFICE 40 ANALYSIS" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Cyan

    $office40 = $snapshot.elements | Where-Object {
        $_.elementType -eq "Room" -and ($_.roomDetails.number -eq "40" -or $_.roomDetails.name -like "*40*")
    }

    if ($office40) {
        Write-Host "Room Information:" -ForegroundColor Green
        Write-Host "  Element ID: $($office40.elementId)" -ForegroundColor White
        Write-Host "  Number: $($office40.roomDetails.number)" -ForegroundColor White
        Write-Host "  Name: $($office40.name)" -ForegroundColor White
        Write-Host "  Area: $([math]::Round($office40.roomDetails.area, 2)) sq ft" -ForegroundColor White
        Write-Host "  Perimeter: $([math]::Round($office40.roomDetails.perimeter, 2)) ft" -ForegroundColor White
        Write-Host "  Volume: $([math]::Round($office40.roomDetails.volume, 2)) cu ft" -ForegroundColor White
        Write-Host "  Level: $($office40.roomDetails.level)" -ForegroundColor White

        if ($office40.boundingBox) {
            Write-Host "`nBounding Box:" -ForegroundColor Cyan
            Write-Host "  Min: ($([math]::Round($office40.boundingBox.minX, 2)), $([math]::Round($office40.boundingBox.minY, 2)), $([math]::Round($office40.boundingBox.minZ, 2)))" -ForegroundColor Gray
            Write-Host "  Max: ($([math]::Round($office40.boundingBox.maxX, 2)), $([math]::Round($office40.boundingBox.maxY, 2)), $([math]::Round($office40.boundingBox.maxZ, 2)))" -ForegroundColor Gray
            Write-Host "  Center: ($([math]::Round($office40.boundingBox.centerX, 2)), $([math]::Round($office40.boundingBox.centerY, 2)), $([math]::Round($office40.boundingBox.centerZ, 2)))" -ForegroundColor Gray
        }
    }

    # Find walls around Office 40
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "WALLS NEAR OFFICE 40" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Cyan

    $walls = $snapshot.elements | Where-Object { $_.elementType -eq "Wall" }
    Write-Host "Total walls in view: $($walls.Count)" -ForegroundColor White

    # Find filled regions
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "FILLED REGIONS" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Cyan

    $filledRegions = $snapshot.elements | Where-Object { $_.elementType -eq "FilledRegion" }
    Write-Host "Total filled regions: $($filledRegions.Count)" -ForegroundColor White

    if ($filledRegions) {
        $filledRegions | Select-Object -First 5 | ForEach-Object {
            Write-Host "`nFilled Region ID: $($_.elementId)" -ForegroundColor Cyan
            if ($_.boundingBox) {
                Write-Host "  Area (approx): $([math]::Round(($_.boundingBox.maxX - $_.boundingBox.minX) * ($_.boundingBox.maxY - $_.boundingBox.minY), 2)) sq ft" -ForegroundColor Gray
                Write-Host "  Center: ($([math]::Round($_.boundingBox.centerX, 2)), $([math]::Round($_.boundingBox.centerY, 2)))" -ForegroundColor Gray
            }
        }
    }

} else {
    Write-Host "ERROR: $($snapshot.error)" -ForegroundColor Red
}
