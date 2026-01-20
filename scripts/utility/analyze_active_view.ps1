# Analyze the active view in Revit

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

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ANALYZING ACTIVE VIEW IN REVIT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get active view info
Write-Host "Getting active view information..." -ForegroundColor Yellow
$viewResult = Send-RevitCommand -Method "getActiveView" -Params @{}

if ($viewResult.success) {
    Write-Host "`nActive View Details:" -ForegroundColor Green
    Write-Host "  View Name: $($viewResult.viewName)" -ForegroundColor White
    Write-Host "  View Type: $($viewResult.viewType)" -ForegroundColor White
    Write-Host "  View ID: $($viewResult.viewId)" -ForegroundColor White

    if ($viewResult.level) {
        Write-Host "  Level: $($viewResult.level)" -ForegroundColor White
    }
} else {
    Write-Host "ERROR: Could not get active view - $($viewResult.error)" -ForegroundColor Red
    exit
}

# Get rooms in active view
Write-Host "`nGetting rooms in active view..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

if ($roomsResult.success) {
    $viewRooms = $roomsResult.rooms | Where-Object { $_.level -eq $viewResult.level }
    Write-Host "Found $($viewRooms.Count) rooms on this level" -ForegroundColor Green

    if ($viewRooms.Count -gt 0) {
        Write-Host "`nFirst 10 rooms:" -ForegroundColor Cyan
        $viewRooms | Select-Object -First 10 | Format-Table number, name, @{Label='Area (SF)';Expression={[math]::Round($_.area,0)}} -AutoSize
    }
}

# Get filled regions in active view
Write-Host "`nGetting filled regions in active view..." -ForegroundColor Yellow
$regionsResult = Send-RevitCommand -Method "getFilledRegions" -Params @{}

if ($regionsResult.success) {
    if ($regionsResult.filledRegions) {
        Write-Host "Found $($regionsResult.filledRegions.Count) filled regions" -ForegroundColor Green

        if ($regionsResult.filledRegions.Count -gt 0) {
            Write-Host "`nFirst 10 filled regions:" -ForegroundColor Cyan
            $regionsResult.filledRegions | Select-Object -First 10 | Format-Table name, @{Label='Area (SF)';Expression={[math]::Round($_.area,0)}}, @{Label='Adjusted (×1.2)';Expression={[math]::Round($_.area * 1.2,0)}} -AutoSize
        }
    } else {
        Write-Host "No filled regions found in this view" -ForegroundColor Yellow
        Write-Host "  Make sure filled regions are visible in this view" -ForegroundColor Yellow
        Write-Host "  Check View → Visibility/Graphics settings" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: $($regionsResult.error)" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Analysis complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
