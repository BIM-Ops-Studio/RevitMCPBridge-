# Check window schedule
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING WINDOW SCHEDULE ===" -ForegroundColor Cyan

# First get window schedule ID
$json = '{"method":"getSchedules","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Available schedules:"
    $result.result.schedules | Where-Object { $_.name -like "*Window*" -or $_.name -like "*WINDOW*" } | ForEach-Object {
        Write-Host "  $($_.name) (ID: $($_.id))"
    }
}

# Get window schedule data (ID 510941 from earlier session)
Write-Host ""
Write-Host "=== WINDOW SCHEDULE DATA ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleData","params":{"scheduleId":510941}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    # Show headers
    Write-Host "Headers:"
    Write-Host "  Row 0: $($result.result.data[0] -join ' | ')"
    Write-Host "  Row 1: $($result.result.data[1] -join ' | ')"

    # Count windows
    $windowCount = 0
    foreach ($row in $result.result.data) {
        if ($row[0] -match '^\d+$' -or $row[0] -match '^[A-Z]\d*$') {
            $windowCount++
        }
    }
    Write-Host ""
    Write-Host "Total windows in schedule: $windowCount"

    # Show sample
    Write-Host ""
    Write-Host "Sample entries:" -ForegroundColor Yellow
    $result.result.data | Select-Object -Skip 2 -First 10 | ForEach-Object {
        Write-Host "  Mark=$($_[0]) Room=$($_[1])"
    }
} else {
    Write-Host "Error getting window schedule: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
