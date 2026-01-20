# Diagnose Office 40 Room Boundaries
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
Write-Host "Office 40 - Room Boundary Diagnostic" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Get current wall states
Write-Host "Checking current wall configuration..." -ForegroundColor Yellow

$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if (-not $result.success) {
    Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
    exit 1
}

Write-Host "`nCurrent Wall States:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

foreach ($wall in $result.boundaryWalls) {
    Write-Host "`nWall ID: $($wall.wallId) - $($wall.classification)" -ForegroundColor Yellow
    Write-Host "  Type: $($wall.wallType)" -ForegroundColor Gray
    Write-Host "  Adjacent: $($wall.adjacentSpace)" -ForegroundColor Gray
    Write-Host "  Current Location Line: $($wall.currentLocationLine)" -ForegroundColor $(if ($wall.currentLocationLine -eq $wall.recommendedLocationLine) { "Green" } else { "Red" })
    Write-Host "  Room Bounding: $($wall.isRoomBounding)" -ForegroundColor Gray
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "IMPORTANT: Understanding Location Lines" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nFor HALLWAY walls:" -ForegroundColor Yellow
Write-Host "  • FinishFaceExterior = Boundary on the EXTERIOR side of wall" -ForegroundColor White
Write-Host "  • FinishFaceInterior = Boundary on the INTERIOR side of wall" -ForegroundColor White
Write-Host "  • Which side is 'exterior' depends on wall orientation!" -ForegroundColor Red

Write-Host "`nThe issue might be:" -ForegroundColor Yellow
Write-Host "  1. Wall orientation (exterior/interior face reversed)" -ForegroundColor White
Write-Host "  2. Need to use FinishFaceInterior instead of FinishFaceExterior" -ForegroundColor White
Write-Host "  3. Room needs to be regenerated/recomputed`n" -ForegroundColor White

Write-Host "Try this: Let's flip to FinishFaceInterior for hallway walls" -ForegroundColor Cyan
$response = Read-Host "`nDo you want to try FinishFaceInterior for hallway walls? (y/n)"

if ($response -eq "y") {
    Write-Host "`nModifying hallway walls to FinishFaceInterior..." -ForegroundColor Yellow

    $hallwayWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Hallway" }

    foreach ($wall in $hallwayWalls) {
        Write-Host "`nWall $($wall.wallId)..." -ForegroundColor Yellow

        $modResult = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
            wallId = $wall.wallId.ToString()
            locationLine = "FinishFaceInterior"
            roomBounding = $true
        }

        if ($modResult.success) {
            Write-Host "  ✅ Modified to FinishFaceInterior" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Failed: $($modResult.error)" -ForegroundColor Red
        }
    }

    Write-Host "`n✅ Done! Check Room 40 in Revit now." -ForegroundColor Green
}

Write-Host "`n============================================================`n" -ForegroundColor Cyan
