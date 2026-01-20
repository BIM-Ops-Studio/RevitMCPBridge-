# Check overhead door and all door types
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING OVERHEAD DOOR ===" -ForegroundColor Cyan

# Get all doors
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

# Find overhead door
$overheadDoor = $result.doors | Where-Object { $_.familyName -like "*Overhead*" }
if ($overheadDoor) {
    Write-Host "Overhead Door Found:" -ForegroundColor Green
    Write-Host "  ID: $($overheadDoor.doorId)"
    Write-Host "  Mark: $($overheadDoor.mark)"
    Write-Host "  Family: $($overheadDoor.familyName)"
    Write-Host "  Type: $($overheadDoor.typeName)"
    Write-Host "  Level: $($overheadDoor.level)"
    Write-Host "  Room: $($overheadDoor.toRoom)"
} else {
    Write-Host "No overhead door found in getDoors results" -ForegroundColor Yellow
}

# Check if it's in the schedule
Write-Host ""
Write-Host "=== CHECKING SCHEDULE FOR OVERHEAD DOOR ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$foundInSchedule = $false
foreach ($row in $schedResult.result.data) {
    if ($row[0] -eq $overheadDoor.mark -or $row[1] -like "*overhead*" -or $row[1] -like "*garage*" -or $row[1] -like "*PARKING*") {
        Write-Host "Found in schedule: Mark=$($row[0]) Room=$($row[1])"
        $foundInSchedule = $true
    }
}
if (-not $foundInSchedule) {
    Write-Host "Overhead door NOT found in schedule" -ForegroundColor Red
}

# Now list all doors with their embedded type designations
Write-Host ""
Write-Host "=== ALL DOORS WITH TYPE DESIGNATIONS ===" -ForegroundColor Cyan

$doorsByType = @{}
foreach ($door in $result.doors) {
    # Extract type from typeName if it contains TYPE-X
    $typeMatch = [regex]::Match($door.typeName, "TYPE-([A-Z])")
    $embeddedType = if ($typeMatch.Success) { $typeMatch.Groups[1].Value } else { "None" }

    if (-not $doorsByType.ContainsKey($embeddedType)) {
        $doorsByType[$embeddedType] = @()
    }
    $doorsByType[$embeddedType] += @{
        id = $door.doorId
        mark = $door.mark
        family = $door.familyName
        typeName = $door.typeName
    }
}

foreach ($type in ($doorsByType.Keys | Sort-Object)) {
    $doors = $doorsByType[$type]
    Write-Host ""
    Write-Host "TYPE $type ($($doors.Count) doors):" -ForegroundColor Yellow
    $doors | Select-Object -First 3 | ForEach-Object {
        Write-Host "  Mark $($_.mark): $($_.family) - $($_.typeName)"
    }
    if ($doors.Count -gt 3) {
        Write-Host "  ... and $($doors.Count - 3) more"
    }
}

$pipe.Close()
