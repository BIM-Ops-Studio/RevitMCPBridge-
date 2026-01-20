# Check Hardware parameter
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING HDWR COLUMN ===" -ForegroundColor Cyan

# Get schedule data
$json = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

# Show headers
Write-Host "Column headers:"
Write-Host "  $($result.result.data[0] -join ' | ')"
Write-Host "  $($result.result.data[1] -join ' | ')"

# HDWR is column 9
Write-Host ""
Write-Host "Current HDWR values (sample):" -ForegroundColor Yellow
$result.result.data | Select-Object -Skip 3 -First 15 | ForEach-Object {
    Write-Host "  Door $($_[0]): TYPE='$($_[5])' HDWR='$($_[9])'"
}

# Check hardware parameters on door 248
Write-Host ""
Write-Host "Hardware parameters on door 248:" -ForegroundColor Cyan
$paramJson = '{"method":"getParameters","params":{"elementId":1672936}}'
$writer.WriteLine($paramJson)
$paramResponse = $reader.ReadLine()
$paramResult = $paramResponse | ConvertFrom-Json

$paramResult.result.parameters | Where-Object {
    $_.name -like '*HDWR*' -or $_.name -like '*Hardware*' -or $_.name -like '*Set*'
} | ForEach-Object {
    Write-Host "  $($_.name) = '$($_.value)' (ReadOnly: $($_.isReadOnly))"
}

$pipe.Close()
