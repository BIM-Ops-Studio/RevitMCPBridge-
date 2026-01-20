# Check Level 1 doors in detail
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== LEVEL 1 DOORS ===" -ForegroundColor Cyan

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$l1Doors = $result.doors | Where-Object { $_.level -eq "L1" }

Write-Host "Found $($l1Doors.Count) doors on Level 1:"
Write-Host ""

foreach ($door in $l1Doors) {
    Write-Host "Door Mark: $($door.mark)" -ForegroundColor Yellow
    Write-Host "  ID: $($door.doorId)"
    Write-Host "  Family: $($door.familyName)"
    Write-Host "  Type: $($door.typeName)"
    Write-Host "  Room: $($door.toRoom)"
    Write-Host ""
}

# Check schedule data to see if any L1 marks appear
Write-Host "=== CHECKING SCHEDULE FOR L1 DOOR MARKS ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$l1Marks = $l1Doors | ForEach-Object { $_.mark }
Write-Host "L1 door marks: $($l1Marks -join ', ')"

$foundInSchedule = @()
$notFoundInSchedule = @()

foreach ($mark in $l1Marks) {
    $found = $false
    foreach ($row in $schedResult.result.data) {
        if ($row[0] -eq $mark) {
            $found = $true
            $foundInSchedule += $mark
            break
        }
    }
    if (-not $found) {
        $notFoundInSchedule += $mark
    }
}

Write-Host ""
Write-Host "Found in schedule: $($foundInSchedule -join ', ')" -ForegroundColor Green
Write-Host "NOT in schedule: $($notFoundInSchedule -join ', ')" -ForegroundColor Red

$pipe.Close()
