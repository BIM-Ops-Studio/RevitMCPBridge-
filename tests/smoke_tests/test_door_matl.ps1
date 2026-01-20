# Test Door Material parameter
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== TESTING Dr Panel Mat'l Mark PARAMETER ===" -ForegroundColor Cyan

# Test Dr Panel Mat'l Mark parameter
$json = @{
    method = "setParameter"
    params = @{
        elementId = 1672936
        parameterName = "Dr Panel Mat'l Mark"
        value = "WD"
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Dr Panel Mat'l Mark update successful" -ForegroundColor Green

    # Check schedule
    $json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $schedResult = $response | ConvertFrom-Json

    $door248Row = $schedResult.result.data | Where-Object { $_[0] -eq "248" }
    if ($door248Row) {
        Write-Host "Door 248 in schedule: TYPE='$($door248Row[5])' MATL(col6)='$($door248Row[6])' FRAME-MATL(col7)='$($door248Row[7])'"
    }
} else {
    Write-Host "Update failed: $($result.error)" -ForegroundColor Red
}

$pipe.Close()
