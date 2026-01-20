# Get schedule field information
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING SCHEDULE FIELD INFO ===" -ForegroundColor Cyan

# Get schedule info first
$json = '{"method":"getScheduleInfo","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Schedule Info:" -ForegroundColor Green
    $result.result | ConvertTo-Json -Depth 3
} else {
    Write-Host "getScheduleInfo error: $($result.error)" -ForegroundColor Yellow
}

# Try getAvailableSchedulableFields
Write-Host "`n=== AVAILABLE SCHEDULABLE FIELDS ===" -ForegroundColor Cyan
$json = '{"method":"getAvailableSchedulableFields","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Fields count: $($result.result.fields.Count)" -ForegroundColor Green
    # Look for TYPE-related fields
    $result.result.fields | Where-Object { $_.name -like "*TYPE*" -or $_.name -like "*type*" } | ForEach-Object {
        Write-Host "  $($_.name) (ID: $($_.fieldId))"
    }
} else {
    Write-Host "Error: $($result.error)" -ForegroundColor Yellow
}

# Get current schedule data with full headers
Write-Host "`n=== SCHEDULE DATA SAMPLE ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Show first few rows with column mapping
    Write-Host "Headers from row 0-1:"
    Write-Host "  Row 0: $($result.result.data[0] -join ' | ')"
    Write-Host "  Row 1: $($result.result.data[1] -join ' | ')"

    Write-Host "`nColumn 5 (TYPE) values:"
    $result.result.data | Select-Object -Skip 3 -First 10 | ForEach-Object {
        $mark = $_[0]
        $type = $_[5]
        Write-Host "  Door $mark : TYPE = '$type'"
    }
}

$pipe.Close()
