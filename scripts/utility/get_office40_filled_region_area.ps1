# Get filled region area for Office 40
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

Write-Host "`nGetting filled region area for Office 40..." -ForegroundColor Cyan

$result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
    roomId = "1314059"
    multiplier = 1.0  # Use 1.0 to see the actual filled region area without adjustment
}

if ($result.success) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "OFFICE 40 - FILLED REGION AREA" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nRoom: $($result.roomNumber) - $($result.roomName)" -ForegroundColor White
    Write-Host "`nFilled Region Area: $($result.filledRegionArea) SF" -ForegroundColor Cyan
    Write-Host "Original Room Area: $($result.originalRoomArea) SF" -ForegroundColor Gray
    Write-Host "`nDifference: $([math]::Round($result.filledRegionArea - $result.originalRoomArea, 2)) SF" -ForegroundColor Yellow
    Write-Host "`nWith 1.2x multiplier: $([math]::Round($result.filledRegionArea * 1.2, 2)) SF" -ForegroundColor Green
} else {
    Write-Host "`nERROR: $($result.error)" -ForegroundColor Red
    if ($result.error -like "*Unknown method*") {
        Write-Host "`nPlease restart Revit to load the updated add-in." -ForegroundColor Yellow
    }
}
