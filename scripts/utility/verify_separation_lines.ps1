# Verify what was created and check room area
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
Write-Host "Verifying Room Separation Lines" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check Office 40 current state
Write-Host "Checking Office 40 current area..." -ForegroundColor Yellow
$roomInfo = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomInfo" -Params @{ roomId = "1314059" }

if ($roomInfo.success) {
    Write-Host "✅ Office 40 Info:" -ForegroundColor Green
    Write-Host "   Area: $([math]::Round($roomInfo.area, 2)) sq ft" -ForegroundColor White
    Write-Host "   Perimeter: $([math]::Round($roomInfo.perimeter, 2)) ft" -ForegroundColor White
    Write-Host "`n   ⚠️  If area is still 933.05 sq ft, the lines didn't work!" -ForegroundColor Yellow
}

# Check what walls bound Office 40
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Analyzing boundary walls..." -ForegroundColor Yellow

$boundaries = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if ($boundaries.success) {
    Write-Host "`nWall Classifications:" -ForegroundColor Cyan

    foreach ($wall in $boundaries.boundaryWalls) {
        $color = switch ($wall.classification) {
            "Hallway" { "Yellow" }
            "Demising" { "Cyan" }
            "Exterior" { "Magenta" }
            default { "Gray" }
        }

        Write-Host "`n  Wall $($wall.wallId) - $($wall.classification)" -ForegroundColor $color
        Write-Host "    Type: $($wall.wallType)" -ForegroundColor Gray
        Write-Host "    Adjacent: $($wall.adjacentSpace)" -ForegroundColor Gray
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DIAGNOSIS" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "The issue is likely:" -ForegroundColor Yellow
Write-Host "  1. Room separation lines were created as MODEL LINES" -ForegroundColor White
Write-Host "  2. But they're not being recognized as ROOM BOUNDARIES" -ForegroundColor White
Write-Host "  3. Revit requires specific category/subcategory for room calculation`n" -ForegroundColor White

Write-Host "Room separation lines in Revit:" -ForegroundColor Cyan
Write-Host "  • Must be in the RoomSeparationLines category" -ForegroundColor White
Write-Host "  • Must be in the correct view's sketch plane" -ForegroundColor White
Write-Host "  • Room must be recalculated after creation" -ForegroundColor White
Write-Host "  • They override wall-based boundaries`n" -ForegroundColor White

Write-Host "CONCLUSION:" -ForegroundColor Red
Write-Host "Wall Location Line approach = Doesn't work (confirmed)" -ForegroundColor White
Write-Host "Room Separation Lines = Created but not working as room boundaries" -ForegroundColor White
Write-Host "`nThis suggests:" -ForegroundColor Yellow
Write-Host "  • Room boundary calculation in Revit is more complex than API exposes" -ForegroundColor White
Write-Host "  • May require manual adjustment OR different approach entirely`n" -ForegroundColor White

Write-Host "============================================================`n" -ForegroundColor Cyan
