# Test simple ping that doesn't require Revit API
$pipeName = "\\.\pipe\RevitMCPBridge2026"

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    Write-Host "Connecting..." -ForegroundColor Yellow
    $pipe.Connect(5000)
    Write-Host "[CONNECTED]" -ForegroundColor Green

    # Test ping (doesn't require Revit API)
    $request = @{
        method = "ping"
        parameters = @{}
    } | ConvertTo-Json -Compress

    Write-Host "Sending ping..." -ForegroundColor Yellow
    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $writer.WriteLine($request)

    $reader = New-Object System.IO.StreamReader($pipe)
    $response = $reader.ReadLine()

    Write-Host "[RESPONSE]" -ForegroundColor Green
    Write-Host $response -ForegroundColor White

    $reader.Close()
    $writer.Close()
    $pipe.Close()

} catch {
    Write-Host "[FAILED] $_" -ForegroundColor Red
}
