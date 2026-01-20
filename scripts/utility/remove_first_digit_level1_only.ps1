# Remove first digit from Level 1 office room numbers only
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
Write-Host "REMOVE FIRST DIGIT - LEVEL 1 ONLY" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all rooms
Write-Host "Getting all rooms..." -ForegroundColor Cyan
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

if (-not $roomsResult.success) {
    Write-Host "ERROR: Could not get rooms - $($roomsResult.error)" -ForegroundColor Red
    exit
}

# Filter for Level 1 offices only
$level1Offices = $roomsResult.rooms | Where-Object {
    $_.name -like "*OFFICE*" -and $_.level -eq "L1"
}

Write-Host "Found $($level1Offices.Count) offices on Level 1`n" -ForegroundColor Green

$successCount = 0
$errorCount = 0
$skippedCount = 0

foreach ($office in $level1Offices) {
    $currentNumber = $office.number

    # Remove first digit if number has more than 1 digit
    if ($currentNumber.Length -gt 1) {
        $newNumber = $currentNumber.Substring(1)

        Write-Host "Processing: Room $currentNumber -> $newNumber" -ForegroundColor White

        $result = Send-RevitCommand -Method "modifyRoomProperties" -Params @{
            roomId = $office.roomId.ToString()
            number = $newNumber
        }

        if ($result.success) {
            $successCount++
            Write-Host "  SUCCESS: $currentNumber -> $newNumber" -ForegroundColor Green
        } else {
            $errorCount++
            Write-Host "  ERROR: $($result.error)" -ForegroundColor Red
        }
    } else {
        $skippedCount++
        Write-Host "Skipping: Room $currentNumber (already single digit)" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY - LEVEL 1 ONLY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Level 1 Offices: $($level1Offices.Count)" -ForegroundColor White
Write-Host "Successfully Renumbered: $successCount" -ForegroundColor Green
Write-Host "Skipped (already single digit): $skippedCount" -ForegroundColor Gray
Write-Host "Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Gray" })

Write-Host "`nDone!" -ForegroundColor Green
