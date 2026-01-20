# MCP Test v3
$pipeName = "RevitMCPBridge2026"

Write-Host "MCP Test v3" -ForegroundColor Cyan

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

    Write-Host "Reading response..." -ForegroundColor Yellow
    $response = $reader.ReadLine()

    $pipe.Close()

    if ([string]::IsNullOrEmpty($response)) {
        Write-Host "Empty response - click in Revit drawing area and try again" -ForegroundColor Red
    } else {
        Write-Host "Response:" -ForegroundColor Green
        Write-Host $response

        $obj = $response | ConvertFrom-Json
        if ($obj.success) {
            Write-Host ""
            Write-Host "SUCCESS! MCP is working. Found $($obj.levels.Count) levels." -ForegroundColor Green
        } else {
            Write-Host "Server error: $($obj.error)" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
