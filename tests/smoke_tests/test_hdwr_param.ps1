# Test Hardware parameters
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== TESTING HARDWARE PARAMETERS ===" -ForegroundColor Cyan

# Test Hardware parameter
$json = @{
    method = "setParameter"
    params = @{
        elementId = 1672936
        parameterName = "Hardware"
        value = "HW-1"
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Hardware parameter update successful" -ForegroundColor Green
}

# Check schedule
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$door248Row = $schedResult.result.data | Where-Object { $_[0] -eq "248" }
if ($door248Row) {
    Write-Host "Door 248 in schedule: HDWR(col9)='$($door248Row[9])'"
}

# Try Hardware Set parameter
$json = @{
    method = "setParameter"
    params = @{
        elementId = 1672936
        parameterName = "Hardware Set"
        value = "HW-2"
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Hardware Set parameter update successful" -ForegroundColor Green
}

# Check schedule again
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$schedResult = $response | ConvertFrom-Json

$door248Row = $schedResult.result.data | Where-Object { $_[0] -eq "248" }
if ($door248Row) {
    Write-Host "Door 248 in schedule: HDWR(col9)='$($door248Row[9])'"
}

$pipe.Close()
