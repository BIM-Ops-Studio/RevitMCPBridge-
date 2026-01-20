# Simple pipe connection test
$pipeName = "\\.\pipe\RevitMCPBridge2026"

Write-Host "Testing connection to MCP pipe..." -ForegroundColor Cyan

try {
    # Create pipe client
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)

    Write-Host "Connecting to pipe (5 second timeout)..." -ForegroundColor Yellow
    $pipe.Connect(5000)

    Write-Host "[SUCCESS] Connected to MCP Server!" -ForegroundColor Green

    # Send a simple test request
    $request = @{
        method = "getAllRooms"
        parameters = @{}
    } | ConvertTo-Json -Compress

    Write-Host "Sending request: $request" -ForegroundColor Yellow

    $writer = New-Object System.IO.StreamWriter($pipe)
    $writer.AutoFlush = $true
    $writer.WriteLine($request)

    Write-Host "Waiting for response..." -ForegroundColor Yellow

    $reader = New-Object System.IO.StreamReader($pipe)
    $response = $reader.ReadLine()

    Write-Host "[RESPONSE RECEIVED]" -ForegroundColor Green
    Write-Host $response -ForegroundColor White

    $reader.Close()
    $writer.Close()
    $pipe.Close()

} catch {
    Write-Host "[FAILED] Error: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nTest complete." -ForegroundColor Cyan
