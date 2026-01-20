# Simple connection test for RevitMCPBridge2026
# Tests if the named pipe is accessible

$pipeName = "RevitMCPBridge2026"

Write-Host "Testing connection to RevitMCPBridge2026..." -ForegroundColor Cyan

$pipeClient = $null
$writer = $null
$reader = $null

try {
    # Create named pipe client
    Write-Host "Creating pipe client..." -ForegroundColor Yellow
    $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)

    # Connect with 5 second timeout
    Write-Host "Connecting to pipe (5 second timeout)..." -ForegroundColor Yellow
    $pipeClient.Connect(5000)

    if (-not $pipeClient.IsConnected) {
        Write-Host "❌ Failed to connect to pipe!" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Connected to pipe successfully!" -ForegroundColor Green

    # Prepare ping request
    $request = @{
        method = "ping"
        params = @{}
    } | ConvertTo-Json -Compress

    Write-Host "`nSending ping command..." -ForegroundColor Yellow
    Write-Host "Request: $request" -ForegroundColor Gray

    # Send request
    $writer = New-Object System.IO.StreamWriter($pipeClient)
    $writer.AutoFlush = $true
    $writer.WriteLine($request)
    Write-Host "✅ Request sent!" -ForegroundColor Green

    # Read response
    Write-Host "`nWaiting for response..." -ForegroundColor Yellow
    $reader = New-Object System.IO.StreamReader($pipeClient)
    $response = $reader.ReadLine()

    if ([string]::IsNullOrEmpty($response)) {
        Write-Host "❌ Empty response from server!" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Received response!" -ForegroundColor Green
    Write-Host "Response: $response" -ForegroundColor Gray

    # Parse response
    $responseObj = $response | ConvertFrom-Json

    if ($responseObj.success) {
        Write-Host "`n============================================" -ForegroundColor Green
        Write-Host "✅ CONNECTION SUCCESSFUL!" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "Result: $($responseObj.result)" -ForegroundColor Cyan
        Write-Host "Timestamp: $($responseObj.timestamp)" -ForegroundColor Cyan
        Write-Host "Test Message: $($responseObj.testMessage)" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ Server returned error: $($responseObj.error)" -ForegroundColor Red
    }
}
catch {
    Write-Host "`n❌ ERROR: $_" -ForegroundColor Red
    Write-Host "Exception Type: $($_.Exception.GetType().FullName)" -ForegroundColor Yellow

    if ($_.Exception.InnerException) {
        Write-Host "Inner Exception: $($_.Exception.InnerException.Message)" -ForegroundColor Yellow
    }
}
finally {
    # Cleanup
    if ($reader -ne $null) {
        try { $reader.Dispose() } catch {}
    }
    if ($writer -ne $null) {
        try { $writer.Dispose() } catch {}
    }
    if ($pipeClient -ne $null) {
        try {
            if ($pipeClient.IsConnected) {
                $pipeClient.Close()
            }
            $pipeClient.Dispose()
        } catch {}
    }
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
