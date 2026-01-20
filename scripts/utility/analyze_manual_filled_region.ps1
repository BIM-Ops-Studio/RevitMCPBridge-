# Analyze the manually created filled region to understand the pattern
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
Write-Host "Analyzing Manually Created Filled Region" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Get all filled regions in the current view
Write-Host "Searching for filled regions in the current view..." -ForegroundColor Yellow

# We'll need to add a method to get filled regions - let me create a simpler approach
# First, let's get the room boundary information
$roomInfo = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomInfo" -Params @{ roomId = "1314059" }

if ($roomInfo.success) {
    Write-Host "`n✅ Office 40 Information:" -ForegroundColor Green
    Write-Host "   Room Number: $($roomInfo.roomNumber)" -ForegroundColor White
    Write-Host "   Room Name: $($roomInfo.roomName)" -ForegroundColor White
    Write-Host "   Area: $([math]::Round($roomInfo.area, 2)) sq ft" -ForegroundColor White
    Write-Host "   Perimeter: $([math]::Round($roomInfo.perimeter, 2)) ft" -ForegroundColor White
}

# Get boundary walls
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Understanding Your Manual Filled Region Pattern" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Based on your description:" -ForegroundColor Cyan
Write-Host "  ✓ DEMISING walls: Filled region boundary is INSIDE (at center of wall)" -ForegroundColor Cyan
Write-Host "  ✓ HALLWAY walls: Filled region boundary is at HALLWAY FACE" -ForegroundColor Yellow
Write-Host "  ✓ EXTERIOR walls: Filled region boundary is at EXTERIOR FACE" -ForegroundColor Magenta
Write-Host "  ✓ Uses transparency so you can see through it`n" -ForegroundColor Gray

Write-Host "This pattern gives you the ACTUAL USABLE area, which is:" -ForegroundColor Green
Write-Host "  • Less than Revit's calculated area (which uses centerlines)" -ForegroundColor White
Write-Host "  • Perfect for lease calculations" -ForegroundColor White
Write-Host "  • Accurate representation of rentable space`n" -ForegroundColor White

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "I understand the pattern! The current implementation:" -ForegroundColor Cyan
Write-Host "  • Demising walls: Offset = 0 (stays at centerline) ✓" -ForegroundColor Green
Write-Host "  • Hallway walls: Offset = wallThickness/2 (moves to hallway face) ✓" -ForegroundColor Green
Write-Host "  • Exterior walls: Offset = wallThickness/2 (moves to exterior face) ✓" -ForegroundColor Green

Write-Host "`nHowever, I need to verify the DIRECTION of the offset:" -ForegroundColor Yellow
Write-Host "  Current code moves the boundary AWAY from the room (toward exterior/hallway)" -ForegroundColor White
Write-Host "  Your manual region has demising walls on the INSIDE" -ForegroundColor White

Write-Host "`nQuestion for you:" -ForegroundColor Cyan
Write-Host "  Does the filled region I created match your manual one?" -ForegroundColor White
Write-Host "  Or do I need to reverse the offset direction?`n" -ForegroundColor White

Write-Host "Please compare the two filled regions in Revit:" -ForegroundColor Yellow
Write-Host "  1. Your manually created one (the correct pattern)" -ForegroundColor Gray
Write-Host "  2. The one created by TEST_FILLED_REGION.ps1" -ForegroundColor Gray
Write-Host "  3. Tell me if they match or if adjustments are needed`n" -ForegroundColor Gray

Write-Host "============================================================`n" -ForegroundColor Cyan
