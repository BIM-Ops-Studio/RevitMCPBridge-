# Update all door Hardware Set values based on TYPE
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING DOOR HARDWARE ===" -ForegroundColor Cyan
Write-Host "Hardware Legend:"
Write-Host "  HW-A = Entry hardware (keyed)"
Write-Host "  HW-B = Passage set (halls, living)"
Write-Host "  HW-C = Pocket door hardware"
Write-Host "  HW-D = Privacy set (bath, bedroom)"

# Get all doors with their current TYPE from schedule
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

# Build lookup from Mark to TYPE and Room
$doorInfo = @{}
if ($schedResult.success) {
    foreach ($row in $schedResult.result.data) {
        if ($row[0] -match '^\d+$') {
            $doorInfo[$row[0]] = @{
                type = $row[5]
                room = $row[1]
            }
        }
    }
}

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

if ($doorsResult.success) {
    Write-Host "Found $($doorsResult.doorCount) doors"

    $successCount = 0
    $failCount = 0

    foreach ($door in $doorsResult.doors) {
        # Only process numeric-marked doors
        if ($door.mark -match '^\d+$') {
            $doorId = $door.doorId
            $mark = $door.mark
            $hwSet = "HW-B"  # Default to passage

            # Get TYPE from schedule
            $doorType = ""
            $roomName = ""
            if ($doorInfo.ContainsKey($mark)) {
                $doorType = $doorInfo[$mark].type
                $roomName = $doorInfo[$mark].room
            }

            # Also use toRoom from door data
            if ($roomName -eq "" -and $door.toRoom) {
                $roomName = $door.toRoom
            }

            # Determine hardware set based on TYPE and room
            if ($doorType -eq "A") {
                $hwSet = "HW-A"  # Entry hardware
            }
            elseif ($doorType -eq "C") {
                $hwSet = "HW-C"  # Pocket door hardware
            }
            elseif ($roomName -like "*BATH*" -or $roomName -like "*BEDROOM*" -or $roomName -like "*MASTER*") {
                $hwSet = "HW-D"  # Privacy set for bathrooms and bedrooms
            }
            else {
                $hwSet = "HW-B"  # Passage set for halls, living, kitchen
            }

            # Update Hardware Set
            $updateJson = @{
                method = "setParameter"
                params = @{
                    elementId = $doorId
                    parameterName = "Hardware Set"
                    value = $hwSet
                }
            } | ConvertTo-Json -Compress

            $writer.WriteLine($updateJson)
            $response = $reader.ReadLine()
            $result = $response | ConvertFrom-Json

            if ($result.success) {
                $successCount++
                Write-Host "  Door $mark : HDWR = $hwSet ($roomName)" -ForegroundColor Green
            } else {
                $failCount++
                Write-Host "  Door $mark : FAILED - $($result.error)" -ForegroundColor Red
            }
        }
    }

    Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
    Write-Host "Successfully updated: $successCount doors"
    if ($failCount -gt 0) {
        Write-Host "Failed: $failCount doors" -ForegroundColor Red
    }

    # Summary
    Write-Host "`nHardware Summary:"
    $hwCounts = @{
        "HW-A" = 0
        "HW-B" = 0
        "HW-C" = 0
        "HW-D" = 0
    }
}

$pipe.Close()
