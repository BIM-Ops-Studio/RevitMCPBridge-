# Update Office 40 area from filled region
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
Write-Host "UPDATE OFFICE 40 AREA FROM FILLED REGION" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Update Office 40 area (multiply filled region by 1.2)
$result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
    roomId = "1314059"
    multiplier = 1.2
}

if ($result.success) {
    Write-Host "SUCCESS! Updated Office 40 area" -ForegroundColor Green
    Write-Host "`nRoom Information:" -ForegroundColor Cyan
    Write-Host "  Room Number: $($result.roomNumber)" -ForegroundColor White
    Write-Host "  Room Name: $($result.roomName)" -ForegroundColor White
    Write-Host "`nArea Calculation:" -ForegroundColor Cyan
    Write-Host "  Original Room Area: $($result.originalRoomArea) SF" -ForegroundColor Gray
    Write-Host "  Filled Region Area: $($result.filledRegionArea) SF" -ForegroundColor White
    Write-Host "  Multiplier: $($result.multiplier)x" -ForegroundColor White
    Write-Host "  Adjusted Area: $($result.adjustedArea) SF" -ForegroundColor Green
    Write-Host "`nComments Parameter Updated: $($result.commentsUpdated)" -ForegroundColor Yellow
    Write-Host "`nFilled Region ID: $($result.filledRegionId)" -ForegroundColor Gray
} else {
    Write-Host "ERROR: $($result.error)" -ForegroundColor Red
    if ($result.stackTrace) {
        Write-Host "`nStack Trace:" -ForegroundColor Gray
        Write-Host $result.stackTrace -ForegroundColor DarkGray
    }
}
