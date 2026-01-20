# MCP Test v2 - with timeout handling
$pipeName = "RevitMCPBridge2026"

Write-Host "MCP Test v2" -ForegroundColor Cyan

$json = '{"method":"getLevels","params":{}}'
Write-Host "Request: $json"

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    Write-Host "Connecting..." -ForegroundColor Yellow
    $pipe.Connect(10000)
    Write-Host "Connected!" -ForegroundColor Green

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    Write-Host "Sending request..." -ForegroundColor Yellow
    $writer.WriteLine($json)

    Write-Host "Waiting for response (up to 30 seconds)..." -ForegroundColor Yellow

    # Set read timeout
    $pipe.ReadTimeout = 30000

    $response = $reader.ReadLine()

    if ([string]::IsNullOrEmpty($response)) {
        Write-Host "Empty response received" -ForegroundColor Red
    } else {
        Write-Host "Response:" -ForegroundColor Green
        Write-Host $response

        $obj = $response | ConvertFrom-Json
        if ($obj.success) {
            Write-Host ""
            Write-Host "SUCCESS! Found $($obj.levels.Count) levels." -ForegroundColor Green
        } else {
            Write-Host "Error: $($obj.error)" -ForegroundColor Red
        }
    }

    $pipe.Close()
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception.GetType().FullName
}

Write-Host ""
Write-Host "Make sure:" -ForegroundColor Yellow
Write-Host "1. A Revit project is open (not just Revit startup screen)"
Write-Host "2. Click somewhere in the Revit drawing area first"
Write-Host "3. The MCP Tools ribbon is visible"
