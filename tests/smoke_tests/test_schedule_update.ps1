# Test schedule cell update with different parameter formats
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(30000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== TESTING SCHEDULE CELL UPDATE ===" -ForegroundColor Cyan

# Try different parameter formats
$testParams = @(
    '{"method":"updateScheduleCell","params":{"scheduleId":1487966,"row":4,"column":5,"value":"D"}}',
    '{"method":"updateScheduleCell","params":{"scheduleId":1487966,"row":4,"col":5,"value":"D"}}',
    '{"method":"setScheduleCellValue","params":{"scheduleId":1487966,"row":4,"column":5,"value":"D"}}',
    '{"method":"modifyScheduleCell","params":{"scheduleId":1487966,"row":4,"column":5,"value":"D"}}'
)

foreach ($json in $testParams) {
    Write-Host "`nTrying: $json"
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json
    if ($result.success) {
        Write-Host "  SUCCESS!" -ForegroundColor Green
    } else {
        Write-Host "  Error: $($result.error)" -ForegroundColor Yellow
    }
}

# Also try to get the list of available methods
Write-Host "`n--- Checking for method list ---" -ForegroundColor Cyan
$json = '{"method":"listMethods","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json
if ($result.success) {
    Write-Host "Available methods containing 'schedule' or 'door':"
    # Would need to filter the methods list
}

$pipe.Close()
