# Update all door TYPE values based on legend
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING ALL DOOR TYPES ===" -ForegroundColor Cyan
Write-Host "Type Legend:"
Write-Host "  TYPE A = Entry door"
Write-Host "  TYPE B = Entry door (alternate)"
Write-Host "  TYPE C = Interior Pocket door"
Write-Host "  TYPE D = Interior swing door"

# Get schedule data for room and width info
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

# Build a lookup from Mark to schedule info
$scheduleInfo = @{}
if ($schedResult.success) {
    foreach ($row in $schedResult.result.data) {
        if ($row[0] -match '^\d+$') {
            $mark = $row[0]
            $roomName = $row[1]
            $width = $row[2]
            $scheduleInfo[$mark] = @{
                roomName = $roomName
                width = $width
            }
        }
    }
    Write-Host "`nLoaded schedule info for $($scheduleInfo.Count) doors" -ForegroundColor Green
}

# Get all doors from model
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

if ($doorsResult.success) {
    Write-Host "Found $($doorsResult.doorCount) doors in model"

    $updates = @{
        "A" = @()
        "B" = @()
        "C" = @()
        "D" = @()
    }
    $toUpdate = @()

    foreach ($door in $doorsResult.doors) {
        # Only process numeric-marked doors
        if ($door.mark -match '^\d+$') {
            $mark = $door.mark
            $doorId = $door.doorId
            $roomName = ""
            $width = ""

            # Get room/width from schedule info
            if ($scheduleInfo.ContainsKey($mark)) {
                $roomName = $scheduleInfo[$mark].roomName
                $width = $scheduleInfo[$mark].width
            }

            # Also use toRoom from door data if schedule info is empty
            if ($roomName -eq "" -and $door.toRoom) {
                $roomName = $door.toRoom
            }

            # Determine type based on room and width
            $assignedType = "D"  # Default to interior

            # Entry doors - room name contains ENTRY
            if ($roomName -like "*ENTRY*") {
                $assignedType = "A"
            }
            # Pocket doors - 2'-10" (34") in bedrooms
            elseif ($width -like "*2' - 10*" -and ($roomName -like "*BEDROOM*" -or $roomName -like "*MASTER*")) {
                $assignedType = "C"
            }

            $updates[$assignedType] += @{
                id = $doorId
                mark = $mark
                room = $roomName
            }

            $toUpdate += @{
                id = $doorId
                mark = $mark
                type = $assignedType
            }
        }
    }

    # Summary
    Write-Host "`n=== TYPE ASSIGNMENTS ===" -ForegroundColor Yellow
    Write-Host "TYPE A (Entry): $($updates['A'].Count) doors"
    $updates['A'] | ForEach-Object { Write-Host "  Door $($_.mark) ($($_.room))" }

    Write-Host "`nTYPE C (Pocket): $($updates['C'].Count) doors"
    $updates['C'] | ForEach-Object { Write-Host "  Door $($_.mark) ($($_.room))" }

    Write-Host "`nTYPE D (Interior): $($updates['D'].Count) doors"

    $total = $updates['A'].Count + $updates['C'].Count + $updates['D'].Count
    Write-Host "`nTotal to update: $total doors"

    # Now update all doors
    Write-Host "`n=== UPDATING DOORS ===" -ForegroundColor Cyan
    $successCount = 0
    $failCount = 0

    foreach ($door in $toUpdate) {
        $updateJson = @{
            method = "setParameter"
            params = @{
                elementId = $door.id
                parameterName = "Dr Panel Type"
                value = $door.type
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($updateJson)
        $updateResponse = $reader.ReadLine()
        $updateResult = $updateResponse | ConvertFrom-Json

        if ($updateResult.success) {
            $successCount++
            Write-Host "  Door $($door.mark) -> TYPE $($door.type)" -ForegroundColor Green
        } else {
            $failCount++
            Write-Host "  Door $($door.mark) FAILED: $($updateResult.error)" -ForegroundColor Red
        }
    }

    Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
    Write-Host "Successfully updated: $successCount doors"
    if ($failCount -gt 0) {
        Write-Host "Failed: $failCount doors" -ForegroundColor Red
    }
}

$pipe.Close()
