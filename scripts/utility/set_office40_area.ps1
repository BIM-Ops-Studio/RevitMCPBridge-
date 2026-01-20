# Set Office 40 Comments parameter with 1.2x filled region area
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

Write-Host "`nUpdating Office 40 Comments parameter..." -ForegroundColor Cyan

$result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
    roomId = "1314059"
    multiplier = 1.2
}

if ($result.success) {
    Write-Host "`nSUCCESS! Office 40 Comments parameter updated" -ForegroundColor Green
    Write-Host "`nFilled Region Area: $($result.filledRegionArea) SF" -ForegroundColor White
    Write-Host "Multiplied by 1.2: $($result.adjustedArea) SF" -ForegroundColor White
    Write-Host "`nComments Parameter Set To: $([math]::Round($result.adjustedArea, 0)) SF" -ForegroundColor Cyan
} else {
    Write-Host "`nERROR: $($result.error)" -ForegroundColor Red
}
