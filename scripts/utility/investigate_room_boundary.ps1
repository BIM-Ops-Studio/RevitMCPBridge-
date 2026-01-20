# Investigate why room boundaries aren't changing
function Send-RevitCommand {
    param([string]$PipeName, [string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        if (-not $pipeClient.IsConnected) { throw "Failed to connect" }
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        if ([string]::IsNullOrEmpty($response)) { throw "Empty response" }
        return $response | ConvertFrom-Json
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Investigating Room Boundary Issue" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check wall info
Write-Host "Checking Wall 1307543 (hallway wall) parameters..." -ForegroundColor Yellow
$wallInfo = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getWallInfo" -Params @{ wallId = "1307543" }

if ($wallInfo.success) {
    Write-Host "`nWall Info:" -ForegroundColor Cyan
    Write-Host ($wallInfo | ConvertTo-Json -Depth 3)
} else {
    Write-Host "❌ Failed to get wall info: $($wallInfo.error)" -ForegroundColor Red
}

# Check room info
Write-Host "`n`nChecking Office 40 room info..." -ForegroundColor Yellow
$roomInfo = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomInfo" -Params @{ roomId = "1314059" }

if ($roomInfo.success) {
    Write-Host "`nRoom Info:" -ForegroundColor Cyan
    Write-Host "  Area: $($roomInfo.area) sq ft" -ForegroundColor White
    Write-Host "  Perimeter: $($roomInfo.perimeter) ft" -ForegroundColor White
    Write-Host "  Volume: $($roomInfo.volume) cu ft" -ForegroundColor White
} else {
    Write-Host "❌ Failed to get room info: $($roomInfo.error)" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DISCOVERY" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "The issue: Wall Location Line does NOT control room boundaries!" -ForegroundColor Red
Write-Host "`nIn Revit, room boundaries are calculated from:" -ForegroundColor Yellow
Write-Host "  1. The PHYSICAL wall geometry (not location line)" -ForegroundColor White
Write-Host "  2. Room boundary lines (separate elements)" -ForegroundColor White
Write-Host "  3. Room boundary offset parameter on the ROOM" -ForegroundColor White

Write-Host "`nThe Wall Location Line parameter only affects:" -ForegroundColor Yellow
Write-Host "  • Where dimensions attach to the wall" -ForegroundColor White
Write-Host "  • Wall positioning relative to sketch line" -ForegroundColor White
Write-Host "  • NOT room boundary calculation!`n" -ForegroundColor Red

Write-Host "To control room boundaries, we need to:" -ForegroundColor Cyan
Write-Host "  Option 1: Use Room Separation Lines" -ForegroundColor White
Write-Host "  Option 2: Set room boundary offset on the room itself" -ForegroundColor White
Write-Host "  Option 3: Modify the actual wall geometry/thickness`n" -ForegroundColor White

Write-Host "============================================================`n" -ForegroundColor Cyan
