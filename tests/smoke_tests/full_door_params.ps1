# Get ALL parameters on a door element
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== ALL DOOR PARAMETERS ===" -ForegroundColor Cyan

# Get parameters for door 248 (ID 1672936)
$json = '{"method":"getParameters","params":{"elementId":1672936}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Total parameters: $($result.result.parameters.Count)" -ForegroundColor Green

    # Show all writable text parameters
    Write-Host "`n=== All Writable Parameters (potential TYPE candidates) ===" -ForegroundColor Yellow
    $result.result.parameters | Where-Object { $_.isReadOnly -eq $false } | ForEach-Object {
        Write-Host "  $($_.name) = '$($_.value)'"
    }
}

# Also check schedule fields
Write-Host "`n=== SCHEDULE FIELDS ===" -ForegroundColor Cyan
$json = '{"method":"getScheduleFields","params":{"scheduleId":1487966}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Schedule fields:"
    $result.result.fields | ForEach-Object {
        Write-Host "  Index $($_.fieldIndex): $($_.name) (Hidden: $($_.isHidden))"
    }
}

$pipe.Close()
