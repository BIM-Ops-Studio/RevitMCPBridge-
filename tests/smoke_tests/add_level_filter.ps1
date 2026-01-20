# Add level filter to show only L1 and L2
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== ADDING LEVEL FILTER ===" -ForegroundColor Cyan

# First, we need to add the Level field to the schedule if not present
# Then filter by Level <= L2

# Try to add a filter - need to use "Level" field
# Filter type options: Equal, NotEqual, GreaterThan, LessThan, GreaterOrEqual, LessOrEqual, Contains, NotContains, BeginsWith, EndsWith

# Add filter to exclude L3
$json = @{
    method = "addScheduleFilter"
    params = @{
        scheduleId = 1487966
        fieldName = "Level"
        filterType = "NotEqual"
        value = "L3"
    }
} | ConvertTo-Json -Compress

Write-Host "Adding filter: Level != L3"
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Filter added: Level != L3" -ForegroundColor Green
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

# Add filter to exclude L4
$json = @{
    method = "addScheduleFilter"
    params = @{
        scheduleId = 1487966
        fieldName = "Level"
        filterType = "NotEqual"
        value = "L4"
    }
} | ConvertTo-Json -Compress

Write-Host "Adding filter: Level != L4"
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Filter added: Level != L4" -ForegroundColor Green
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Red
}

# Verify filters
Write-Host ""
Write-Host "=== VERIFYING FILTERS ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleFilters","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Current filters:"
    $result.result.filters | ForEach-Object {
        Write-Host "  $($_.fieldHeading) $($_.filterType) '$($_.value)'"
    }
}

# Check schedule data count
Write-Host ""
Write-Host "=== CHECKING SCHEDULE DATA ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$doorCount = 0
foreach ($row in $schedResult.result.data) {
    if ($row[0] -match '^[A-Z]$') {
        $doorCount++
    }
}
Write-Host "Doors in filtered schedule: $doorCount"

$pipe.Close()
