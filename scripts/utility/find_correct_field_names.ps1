# Try different field name variations to find what works
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
Write-Host "FIND CORRECT ROOM FIELD NAMES" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Create a test schedule
Write-Host "Creating test schedule..." -ForegroundColor Cyan
$createResult = Send-RevitCommand -Method "createSchedule" -Params @{
    scheduleName = "Test Field Names"
    category = "Rooms"
}

if (-not $createResult.success) {
    Write-Host "ERROR: Could not create test schedule - $($createResult.error)" -ForegroundColor Red
    exit
}

$scheduleId = $createResult.scheduleId
Write-Host "Test schedule created (ID: $scheduleId)`n" -ForegroundColor Green

# Field name variations to try
$fieldVariations = @{
    "Room Number" = @("Number", "Room Number", "ROOM_NUMBER", "Room_Number")
    "Room Name" = @("Name", "Room Name", "ROOM_NAME", "Room_Name")
    "Level" = @("Level", "LEVEL", "Room Level", "ROOM_LEVEL")
    "Area" = @("Area", "AREA", "Room Area", "ROOM_AREA")
    "Comments" = @("Comments", "Comment", "COMMENTS", "COMMENT", "All Model Instance Comments")
}

$successfulFields = @{}

foreach ($fieldType in $fieldVariations.Keys) {
    Write-Host "Testing '$fieldType'..." -ForegroundColor Cyan
    $found = $false

    foreach ($variation in $fieldVariations[$fieldType]) {
        Write-Host "  Trying '$variation'..." -ForegroundColor Gray

        $result = Send-RevitCommand -Method "addScheduleField" -Params @{
            scheduleId = $scheduleId.ToString()
            fieldName = $variation
        }

        if ($result.success) {
            Write-Host "    ✓ SUCCESS: '$variation' works!" -ForegroundColor Green
            $successfulFields[$fieldType] = $variation
            $found = $true
            break
        }
    }

    if (-not $found) {
        Write-Host "    ✗ FAILED: None of the variations worked" -ForegroundColor Red
    }
}

# Delete the test schedule
Write-Host "`nCleaning up test schedule..." -ForegroundColor Cyan
$deleteResult = Send-RevitCommand -Method "deleteSchedule" -Params @{
    scheduleId = $scheduleId.ToString()
}

if ($deleteResult.success) {
    Write-Host "Test schedule deleted`n" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not delete test schedule`n" -ForegroundColor Yellow
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CORRECT FIELD NAMES FOUND" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

if ($successfulFields.Count -gt 0) {
    foreach ($fieldType in $successfulFields.Keys) {
        Write-Host "$fieldType => '$($successfulFields[$fieldType])'" -ForegroundColor Green
    }

    Write-Host "`nUse these exact field names in your schedule creation script." -ForegroundColor White
} else {
    Write-Host "No working field names found. May need to restart Revit or check schedule category." -ForegroundColor Red
}

Write-Host "`nDone!" -ForegroundColor Green
