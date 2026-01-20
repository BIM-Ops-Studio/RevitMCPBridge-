# Office 40 - Final Fix After Wall Flip
# User flipped walls so exterior faces point to hallway
# Now FinishFaceExterior should work correctly

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
Write-Host "Office 40 - Final Configuration" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "User action: Flipped walls so exterior faces → hallway" -ForegroundColor Yellow
Write-Host "Now applying: FinishFaceExterior for hallway walls`n" -ForegroundColor Yellow

# Get all boundary walls
$wallsResult = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if (-not $wallsResult.success) {
    Write-Host "❌ Failed: $($wallsResult.error)" -ForegroundColor Red
    exit 1
}

$hallwayWalls = $wallsResult.boundaryWalls | Where-Object { $_.classification -eq "Hallway" }
$demisingWalls = $wallsResult.boundaryWalls | Where-Object { $_.classification -eq "Demising" }

Write-Host "Applying configuration:" -ForegroundColor Cyan
Write-Host "  • Demising walls ($($demisingWalls.Count)) → WallCenterline" -ForegroundColor White
Write-Host "  • Hallway walls ($($hallwayWalls.Count)) → FinishFaceExterior`n" -ForegroundColor White

# Demising walls
foreach ($wall in $demisingWalls) {
    Write-Host "Wall $($wall.wallId) (Demising) → WallCenterline..." -ForegroundColor Yellow
    $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
        wallId = $wall.wallId.ToString()
        locationLine = "WallCenterline"
        roomBounding = $true
    }
    if ($result.success) {
        Write-Host "  ✅ SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $($result.error)" -ForegroundColor Red
    }
}

# Hallway walls
foreach ($wall in $hallwayWalls) {
    Write-Host "Wall $($wall.wallId) (Hallway) → FinishFaceExterior..." -ForegroundColor Yellow
    $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
        wallId = $wall.wallId.ToString()
        locationLine = "FinishFaceExterior"
        roomBounding = $true
    }
    if ($result.success) {
        Write-Host "  ✅ SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $($result.error)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Configuration Applied!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "What this means:" -ForegroundColor Yellow
Write-Host "  • Demising walls: Boundary at wall CENTER" -ForegroundColor White
Write-Host "  • Hallway walls: Boundary on EXTERIOR face (hallway side)" -ForegroundColor White
Write-Host "`nSince exterior face now points TO hallway," -ForegroundColor Yellow
Write-Host "the boundary should be ON THE HALLWAY SIDE of these walls." -ForegroundColor Yellow
Write-Host "`nThis means the room will be SMALLER (boundary pushed toward hallway).`n" -ForegroundColor White

Write-Host "If this is WRONG (you want boundary on office side), then:" -ForegroundColor Red
Write-Host "  → Flip walls back OR use FinishFaceInterior instead`n" -ForegroundColor Red

# Export view to verify
Write-Host "Exporting view for verification..." -ForegroundColor Cyan
$exportResult = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "exportViewImage" -Params @{
    outputPath = "D:\RevitMCPBridge2026\office40_after_fix.png"
}

if ($exportResult.success) {
    Write-Host "✅ View exported: office40_after_fix.png" -ForegroundColor Green
    Write-Host "   Check this image to see the room boundaries`n" -ForegroundColor Gray
}

Write-Host "============================================================`n" -ForegroundColor Cyan
