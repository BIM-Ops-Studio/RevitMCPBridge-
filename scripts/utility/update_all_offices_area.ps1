# Update all offices with filled region area x 1.2
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
Write-Host "UPDATE ALL OFFICES - FILLED REGION AREAS" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all rooms in the active view
Write-Host "Getting all rooms..." -ForegroundColor Cyan
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

if (-not $roomsResult.success) {
    Write-Host "ERROR: Could not get rooms - $($roomsResult.error)" -ForegroundColor Red
    exit
}

# Filter for offices only
$offices = $roomsResult.rooms | Where-Object { $_.name -like "*OFFICE*" }

Write-Host "Found $($offices.Count) offices to process`n" -ForegroundColor Green

$successCount = 0
$errorCount = 0
$results = @()

foreach ($office in $offices) {
    Write-Host "Processing: Room $($office.number) - $($office.name)" -ForegroundColor White

    $result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
        roomId = $office.roomId.ToString()
        multiplier = 1.2
    }

    if ($result.success) {
        $successCount++
        $adjustedRounded = [math]::Round($result.adjustedArea, 0)
        $filledRounded = [math]::Round($result.filledRegionArea, 2)
        Write-Host "  SUCCESS: Updated to $adjustedRounded SF (from $filledRounded SF filled region)" -ForegroundColor Green

        $results += [PSCustomObject]@{
            RoomNumber = $office.number
            RoomName = $office.name
            OriginalArea = [math]::Round($result.originalRoomArea, 2)
            FilledRegionArea = [math]::Round($result.filledRegionArea, 2)
            AdjustedArea = [math]::Round($result.adjustedArea, 0)
            Status = "Success"
        }
    } else {
        $errorCount++
        Write-Host "  ERROR: $($result.error)" -ForegroundColor Red

        $results += [PSCustomObject]@{
            RoomNumber = $office.number
            RoomName = $office.name
            OriginalArea = [math]::Round($office.area, 2)
            FilledRegionArea = "N/A"
            AdjustedArea = "N/A"
            Status = "Error"
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Offices: $($offices.Count)" -ForegroundColor White
Write-Host "Successfully Updated: $successCount" -ForegroundColor Green
if ($errorCount -gt 0) {
    Write-Host "Errors: $errorCount" -ForegroundColor Red
} else {
    Write-Host "Errors: $errorCount" -ForegroundColor Gray
}

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

Write-Host "`nDone!" -ForegroundColor Green
