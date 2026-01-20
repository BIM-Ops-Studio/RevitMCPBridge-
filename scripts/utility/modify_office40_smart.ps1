# Smart Wall Modification for Office 40
# Uses the new getRoomBoundaryWalls method to automatically classify and modify walls

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

$pipeName = "RevitMCPBridge2026"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Office 40 - Smart Wall Boundary Modification" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Requirements:" -ForegroundColor Yellow
Write-Host "  • Demising walls (between offices) → WallCenterline" -ForegroundColor White
Write-Host "  • Hallway walls → FinishFaceExterior" -ForegroundColor White
Write-Host "  • Exterior walls → FinishFaceExterior`n" -ForegroundColor White

# Step 1: Get Office 40 boundary walls with classification
Write-Host "[1/2] Analyzing Office 40 boundary walls..." -ForegroundColor Cyan

$result = Send-RevitCommand -PipeName $pipeName -Method "getRoomBoundaryWalls" -Params @{
    roomId = "1314059"  # Office 40 Room ID
}

if (-not $result.success) {
    Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
    Write-Host "`nStack Trace:" -ForegroundColor Yellow
    Write-Host $result.stackTrace -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Found $($result.boundaryWallCount) boundary walls" -ForegroundColor Green
Write-Host "   Room: $($result.roomNumber) - $($result.roomName)`n" -ForegroundColor Gray

# Display wall classifications
Write-Host "Wall Classifications:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$demisingWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Demising" }
$hallwayWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Hallway" }
$exteriorWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Exterior" }
$otherWalls = $result.boundaryWalls | Where-Object { $_.classification -ne "Demising" -and $_.classification -ne "Hallway" -and $_.classification -ne "Exterior" }

Write-Host "`nDemising Walls (between offices): $($demisingWalls.Count)" -ForegroundColor Yellow
$demisingWalls | ForEach-Object {
    Write-Host "  Wall $($_.wallId): $($_.wallType)" -ForegroundColor Gray
    Write-Host "    Adjacent: $($_.adjacentSpace)" -ForegroundColor DarkGray
    Write-Host "    Current: $($_.currentLocationLine) → Recommended: $($_.recommendedLocationLine)" -ForegroundColor DarkGray
}

Write-Host "`nHallway Walls: $($hallwayWalls.Count)" -ForegroundColor Yellow
$hallwayWalls | ForEach-Object {
    Write-Host "  Wall $($_.wallId): $($_.wallType)" -ForegroundColor Gray
    Write-Host "    Adjacent: $($_.adjacentSpace)" -ForegroundColor DarkGray
    Write-Host "    Current: $($_.currentLocationLine) → Recommended: $($_.recommendedLocationLine)" -ForegroundColor DarkGray
}

Write-Host "`nExterior Walls: $($exteriorWalls.Count)" -ForegroundColor Yellow
$exteriorWalls | ForEach-Object {
    Write-Host "  Wall $($_.wallId): $($_.wallType)" -ForegroundColor Gray
    Write-Host "    Current: $($_.currentLocationLine) → Recommended: $($_.recommendedLocationLine)" -ForegroundColor DarkGray
}

if ($otherWalls.Count -gt 0) {
    Write-Host "`nOther Walls: $($otherWalls.Count)" -ForegroundColor Yellow
    $otherWalls | ForEach-Object {
        Write-Host "  Wall $($_.wallId): $($_.wallType)" -ForegroundColor Gray
        Write-Host "    Adjacent: $($_.adjacentSpace)" -ForegroundColor DarkGray
        Write-Host "    Current: $($_.currentLocationLine) → Recommended: $($_.recommendedLocationLine)" -ForegroundColor DarkGray
    }
}

# Step 2: Apply modifications
Write-Host "`n[2/2] Applying wall modifications..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$successCount = 0
$failCount = 0

foreach ($wall in $result.boundaryWalls) {
    Write-Host "Modifying Wall $($wall.wallId) ($($wall.classification))..." -ForegroundColor Yellow

    $modResult = Send-RevitCommand -PipeName $pipeName -Method "modifyWallProperties" -Params @{
        wallId = $wall.wallId.ToString()
        locationLine = $wall.recommendedLocationLine
        roomBounding = $true
    }

    if ($modResult.success) {
        Write-Host "  ✅ SUCCESS! Modified: $($modResult.modified -join ', ')" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ❌ Failed: $($modResult.error)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Modification Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nResults:" -ForegroundColor Yellow
Write-Host "  ✅ Successfully modified: $successCount walls" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "  ❌ Failed: $failCount walls" -ForegroundColor Red
}

Write-Host "`nCheck Office 40 in Revit:" -ForegroundColor Cyan
Write-Host "  • Demising walls should now use WallCenterline" -ForegroundColor White
Write-Host "  • Hallway & Exterior walls should use FinishFaceExterior" -ForegroundColor White
Write-Host "  • Room area should recalculate automatically`n" -ForegroundColor White
