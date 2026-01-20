# Test updating door TYPE parameter
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== TESTING TYPE PARAMETER UPDATE ===" -ForegroundColor Cyan

# Test door 248 (ID 1672936)
$testDoorId = 1672936

# Try different possible parameter names
$parameterNames = @("Dr Panel Type", "Door_Type", "TYPE", "DOOR TYPE", "Type", "Frame Type")

foreach ($paramName in $parameterNames) {
    Write-Host "`nTrying parameter: '$paramName'" -ForegroundColor Yellow
    $json = @{
        method = "setParameter"
        params = @{
            elementId = $testDoorId
            parameterName = $paramName
            value = "TEST"
        }
    } | ConvertTo-Json -Compress

    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json

    if ($result.success) {
        Write-Host "  SUCCESS! '$paramName' worked!" -ForegroundColor Green

        # Now check if it shows in schedule
        Write-Host "  Checking schedule..."
        $checkJson = '{"method":"getScheduleData","params":{"scheduleId":1487966}}'
        $writer.WriteLine($checkJson)
        $checkResponse = $reader.ReadLine()
        $checkResult = $checkResponse | ConvertFrom-Json

        if ($checkResult.success) {
            # Find door 248 row
            foreach ($row in $checkResult.result.data) {
                if ($row[0] -eq "248") {
                    Write-Host "  Door 248 TYPE column now: '$($row[5])'" -ForegroundColor Cyan
                    break
                }
            }
        }

        # Reset the value
        $resetJson = @{
            method = "setParameter"
            params = @{
                elementId = $testDoorId
                parameterName = $paramName
                value = ""
            }
        } | ConvertTo-Json -Compress
        $writer.WriteLine($resetJson)
        $reader.ReadLine() | Out-Null

        break
    } else {
        Write-Host "  Failed: $($result.error)" -ForegroundColor Red
    }
}

$pipe.Close()
