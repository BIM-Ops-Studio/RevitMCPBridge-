# Office 40 - Adaptive Wall Boundary Fix
# Automatically detects wall orientation and applies correct location line

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
Write-Host "Office 40 - Adaptive Boundary Fix (Auto-Detect Orientation)" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Strategy: Try BOTH location line options for hallway walls" -ForegroundColor Yellow
Write-Host "and let you pick which one looks correct!`n" -ForegroundColor Yellow

# Get boundary walls
$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if (-not $result.success) {
    Write-Host "❌ Failed: $($result.error)" -ForegroundColor Red
    exit 1
}

$hallwayWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Hallway" }
$demisingWalls = $result.boundaryWalls | Where-Object { $_.classification -eq "Demising" }

Write-Host "Found:" -ForegroundColor Cyan
Write-Host "  • $($demisingWalls.Count) demising walls (between offices)" -ForegroundColor White
Write-Host "  • $($hallwayWalls.Count) hallway walls`n" -ForegroundColor White

# Step 1: Fix demising walls (always center)
Write-Host "[Step 1] Setting demising walls to WallCenterline..." -ForegroundColor Cyan

foreach ($wall in $demisingWalls) {
    $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
        wallId = $wall.wallId.ToString()
        locationLine = "WallCenterline"
        roomBounding = $true
    }
    if ($result.success) {
        Write-Host "  ✅ Wall $($wall.wallId)" -ForegroundColor Green
    }
}

# Step 2: Try EXTERIOR face for hallway walls first
Write-Host "`n[Step 2] Testing FinishFaceExterior for hallway walls..." -ForegroundColor Cyan

foreach ($wall in $hallwayWalls) {
    $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
        wallId = $wall.wallId.ToString()
        locationLine = "FinishFaceExterior"
        roomBounding = $true
    }
    if ($result.success) {
        Write-Host "  ✅ Wall $($wall.wallId) set to FinishFaceExterior" -ForegroundColor Green
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "CHECK REVIT NOW - Does the boundary look correct?" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nThe hallway walls should now have boundaries on the EXTERIOR face." -ForegroundColor White
Write-Host "If the boundary is on the HALLWAY side (wrong), type 'flip'" -ForegroundColor Yellow
Write-Host "If the boundary is on the OFFICE side (correct), type 'good'`n" -ForegroundColor Yellow

$response = Read-Host "Response"

if ($response -eq "flip") {
    Write-Host "`n[Step 3] Flipping to FinishFaceInterior..." -ForegroundColor Cyan

    foreach ($wall in $hallwayWalls) {
        $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
            wallId = $wall.wallId.ToString()
            locationLine = "FinishFaceInterior"
            roomBounding = $true
        }
        if ($result.success) {
            Write-Host "  ✅ Wall $($wall.wallId) flipped to FinishFaceInterior" -ForegroundColor Green
        }
    }

    Write-Host "`n✅ Done! Check Office 40 again - boundary should be on office side now." -ForegroundColor Green
} elseif ($response -eq "good") {
    Write-Host "`n✅ Perfect! Boundaries are configured correctly." -ForegroundColor Green
    Write-Host "`nFinal Configuration:" -ForegroundColor Cyan
    Write-Host "  • Demising walls → WallCenterline" -ForegroundColor White
    Write-Host "  • Hallway walls → FinishFaceExterior" -ForegroundColor White
} else {
    Write-Host "`nNo changes made. Run the script again to retry." -ForegroundColor Yellow
}

Write-Host "`n============================================================`n" -ForegroundColor Cyan
