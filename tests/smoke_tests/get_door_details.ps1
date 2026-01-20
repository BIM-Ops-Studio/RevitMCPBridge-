# Get door schedule data and door types from Revit
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== DOOR AND FRAME SCHEDULE DATA ===" -ForegroundColor Cyan

# Get schedule data from DOOR AND FRAME SCHEDULE (ID: 1487966)
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nSchedule Fields:" -ForegroundColor Yellow
    $result.result.fields | ForEach-Object { Write-Host "  - $_" }

    Write-Host "`nSchedule Data (first 20 rows):" -ForegroundColor Yellow
    $rowCount = 0
    foreach ($row in $result.result.data) {
        if ($rowCount -lt 20) {
            Write-Host "  $($row -join ' | ')"
            $rowCount++
        }
    }
    Write-Host "`nTotal rows: $($result.result.data.Count)"
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

Write-Host "`n=== DOOR TYPES IN MODEL ===" -ForegroundColor Cyan

# Get door types
$json = '{"method":"getDoorTypes","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$doorTypes = $response | ConvertFrom-Json

if ($doorTypes.success) {
    Write-Host "`nDoor Types:" -ForegroundColor Yellow
    foreach ($dt in $doorTypes.result.doorTypes) {
        Write-Host "  ID: $($dt.id) - $($dt.name)"
    }
} else {
    Write-Host "Error getting door types: $($doorTypes.error)" -ForegroundColor Red
}

$pipe.Close()
