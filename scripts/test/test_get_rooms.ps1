# Test getRooms method
$pipeName = "\\\\.\\pipe\\RevitMCPBridge2026"

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    Write-Host "Connecting..." -ForegroundColor Yellow
    $pipe.Connect(5000)
    Write-Host "[CONNECTED]" -ForegroundColor Green

    # Test getRooms
    $request = @{
        method = "getRooms"
        parameters = @{}
    } | ConvertTo-Json -Compress

    Write-Host "Sending getRooms request..." -ForegroundColor Yellow
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $writer.WriteLine($request)

    $reader = New-Object System.IO.StreamReader($pipe)
    $response = $reader.ReadLine()

    Write-Host "[RESPONSE]" -ForegroundColor Green
    Write-Host $response -ForegroundColor White

    # Try to parse it
    $responseObj = $response | ConvertFrom-Json
    Write-Host "`n[PARSED]" -ForegroundColor Cyan
    Write-Host "Success: $($responseObj.success)" -ForegroundColor White
    if ($responseObj.success) {
        Write-Host "Room count: $(($responseObj.rooms | Measure-Object).Count)" -ForegroundColor Green
    } else {
        Write-Host "Error: $($responseObj.error)" -ForegroundColor Red
    }

    $reader.Close()
    $writer.Close()
    $pipe.Dispose()

} catch {
    Write-Host "[FAILED] $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
