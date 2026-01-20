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

Write-Host ""
Write-Host "========================================"
Write-Host "FIND CORRECT ROOM FIELD NAMES"
Write-Host "========================================"
Write-Host ""

# Create test schedule
Write-Host "Creating test schedule..."
$createResult = Send-RevitCommand -Method "createSchedule" -Params @{
    scheduleName = "Test Field Names"
    category = "Rooms"
}

if (-not $createResult.success) {
    Write-Host "ERROR: $($createResult.error)"
    exit
}

$scheduleId = $createResult.scheduleId
Write-Host "Test schedule created (ID: $scheduleId)"
Write-Host ""

# Field variations to try
$fieldVariations = @{
    "Room Number" = @("Number", "Room Number", "ROOM_NUMBER")
    "Room Name" = @("Name", "Room Name", "ROOM_NAME")
    "Level" = @("Level", "Room Level", "ROOM_LEVEL")
    "Area" = @("Area", "Room Area", "ROOM_AREA")
    "Comments" = @("Comments", "Comment", "COMMENTS")
}

$found = @{}

foreach ($fieldType in $fieldVariations.Keys) {
    Write-Host "Testing: $fieldType"

    foreach ($var in $fieldVariations[$fieldType]) {
        Write-Host "  Trying: $var"

        $result = Send-RevitCommand -Method "addScheduleField" -Params @{
            scheduleId = $scheduleId.ToString()
            fieldName = $var
        }

        if ($result.success) {
            Write-Host "    SUCCESS: $var works"
            $found[$fieldType] = $var
            break
        }
    }

    if (-not $found.ContainsKey($fieldType)) {
        Write-Host "    FAILED: No match found"
    }
}

# Delete test schedule
Write-Host ""
Write-Host "Cleaning up..."
$deleteResult = Send-RevitCommand -Method "deleteSchedule" -Params @{
    scheduleId = $scheduleId.ToString()
}

# Summary
Write-Host ""
Write-Host "========================================"
Write-Host "RESULTS"
Write-Host "========================================"

foreach ($key in $found.Keys) {
    Write-Host "$key uses: $($found[$key])"
}

Write-Host ""
Write-Host "Done"
