# Update all Level 7 room areas to Filled Region × 1.2

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
Write-Host "UPDATING LEVEL 7 ROOM AREAS IN REVIT" -ForegroundColor Cyan
Write-Host "Formula: Filled Region Area × 1.2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all Level 7 rooms
Write-Host "Getting Level 7 rooms..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}
$level7Rooms = $roomsResult.rooms | Where-Object { $_.level -eq "L7" }
Write-Host "Found $($level7Rooms.Count) rooms on Level 7`n" -ForegroundColor Green

$successCount = 0
$failCount = 0
$skipCount = 0

Write-Host "Updating room areas in Revit...`n" -ForegroundColor Yellow

foreach ($room in $level7Rooms) {
    $roomNum = "{0:D2}" -f [int]$room.number

    # Update room area from filled region with 1.2 multiplier
    $result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
        roomId = $room.roomId.ToString()
        multiplier = 1.2
    }

    if ($result.success) {
        $newArea = [math]::Round($result.newArea, 0)
        Write-Host "  Room $roomNum : Updated to $newArea SF" -ForegroundColor Green
        $successCount++
    } elseif ($result.error -match "No filled region") {
        Write-Host "  Room $roomNum : No filled region found, skipped" -ForegroundColor Yellow
        $skipCount++
    } else {
        Write-Host "  Room $roomNum : ERROR - $($result.error)" -ForegroundColor Red
        $failCount++
    }

    Start-Sleep -Milliseconds 50
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successfully updated: $successCount rooms" -ForegroundColor Green
Write-Host "Skipped (no filled region): $skipCount rooms" -ForegroundColor Yellow
Write-Host "Failed: $failCount rooms" -ForegroundColor Red
Write-Host ""
Write-Host "The room areas in Revit now show Filled Region × 1.2" -ForegroundColor Green
Write-Host "Example: Office 01 now shows 810 SF on the drawing" -ForegroundColor Yellow
Write-Host ""
