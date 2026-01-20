# Update door TYPE parameter for all doors
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== UPDATING DOOR TYPES ===" -ForegroundColor Cyan

# First get door schedule data to build the mapping
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$doorTypeMap = @{}

foreach ($row in $result.result.data) {
    if ($row[0] -match "^\d+" -and $row[2] -ne "") {
        $doorNum = $row[0]
        $roomName = $row[1]
        $width = $row[2]

        # Entry doors
        if ($roomName -like "*ENTRY*") {
            $doorTypeMap[$doorNum] = "A"  # Entry (all entry doors as A)
        }
        # Pocket doors - 2'-10" in bedrooms
        elseif ($width -like "*2' - 10*" -and ($roomName -like "*BEDROOM*" -or $roomName -like "*MASTER*")) {
            $doorTypeMap[$doorNum] = "C"  # Pocket
        }
        # Interior doors
        else {
            $doorTypeMap[$doorNum] = "D"  # Interior
        }
    }
}

Write-Host "Mapped $($doorTypeMap.Count) doors to types"

# Now update each door's TYPE parameter
# First, try to get doors and update their parameters
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorsResult = $response | ConvertFrom-Json

if ($doorsResult.success -and $doorsResult.result.doors.Count -gt 0) {
    Write-Host "Found $($doorsResult.result.doors.Count) door elements"

    $updated = 0
    foreach ($door in $doorsResult.result.doors) {
        $mark = $door.mark
        if ($doorTypeMap.ContainsKey($mark)) {
            $newType = $doorTypeMap[$mark]

            # Update the door's type parameter
            $updateJson = @{
                method = "setElementParameter"
                params = @{
                    elementId = $door.id
                    parameterName = "Door_Type"
                    value = $newType
                }
            } | ConvertTo-Json -Compress

            $writer.WriteLine($updateJson)
            $updateResponse = $reader.ReadLine()
            $updateResult = $updateResponse | ConvertFrom-Json

            if ($updateResult.success) {
                $updated++
                Write-Host "  Door $mark -> Type $newType" -ForegroundColor Green
            }
        }
    }
    Write-Host "`nUpdated $updated doors"
} else {
    Write-Host "getDoors returned: $($doorsResult.error)" -ForegroundColor Yellow

    # Try alternative: update schedule cells directly
    Write-Host "`nTrying schedule cell update method..."

    # The TYPE column is column index 5 (0-based) in the schedule
    $rowIndex = 0
    foreach ($row in $result.result.data) {
        if ($row[0] -match "^\d+" -and $row[2] -ne "") {
            $doorNum = $row[0]
            if ($doorTypeMap.ContainsKey($doorNum)) {
                $newType = $doorTypeMap[$doorNum]
                Write-Host "  Row $rowIndex : Door $doorNum -> Type $newType"
            }
        }
        $rowIndex++
    }

    Write-Host "`nSchedule cell update would require setScheduleCellValue method"
}

$pipe.Close()
