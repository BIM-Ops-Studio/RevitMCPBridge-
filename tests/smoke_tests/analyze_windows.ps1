# Analyze window schedule
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== WINDOW SCHEDULE DATA ===" -ForegroundColor Cyan

# Get window schedule data (ID: 510941)
$json = '{"method":"getScheduleData","params":{"scheduleId":510941}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nFields:" -ForegroundColor Yellow
    $result.result.fields | ForEach-Object { Write-Host "  - $_" }

    Write-Host "`nFirst 15 rows:" -ForegroundColor Yellow
    $rowCount = 0
    foreach ($row in $result.result.data) {
        if ($rowCount -lt 15) {
            Write-Host "  $($row -join ' | ')"
            $rowCount++
        }
    }
    Write-Host "`nTotal rows: $($result.result.data.Count)"
}

# Also get WINDOW SCHEDULE-TYPES (1487959)
Write-Host "`n=== WINDOW SCHEDULE-TYPES ===" -ForegroundColor Cyan

$json = '{"method":"getScheduleData","params":{"scheduleId":1487959}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nFields:" -ForegroundColor Yellow
    $result.result.fields | ForEach-Object { Write-Host "  - $_" }

    Write-Host "`nAll rows:" -ForegroundColor Yellow
    foreach ($row in $result.result.data) {
        Write-Host "  $($row -join ' | ')"
    }
}

$pipe.Close()
