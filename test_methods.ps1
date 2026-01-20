# Test which methods are available
$pipeName = "RevitMCPBridge2026"

function Send-MCP {
    param([string]$Json)

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    $writer.WriteLine($Json)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response
}

Write-Host "Testing MCP Methods" -ForegroundColor Cyan
Write-Host ""

# Test 1: Known working method
Write-Host "Test 1: getLevels (should work)" -ForegroundColor Yellow
$response = Send-MCP '{"method":"getLevels","params":{}}'
Write-Host "  Response: $($response.Substring(0, [Math]::Min(80, $response.Length)))..." -ForegroundColor Gray
Write-Host ""

# Test 2: New method - getTextTypes
Write-Host "Test 2: getTextTypes (new method)" -ForegroundColor Yellow
$response = Send-MCP '{"method":"getTextTypes","params":{}}'
Write-Host "  Response: $response" -ForegroundColor Gray
Write-Host ""

# Test 3: Non-existent method
Write-Host "Test 3: fakeMethod (should fail gracefully)" -ForegroundColor Yellow
$response = Send-MCP '{"method":"fakeMethod","params":{}}'
Write-Host "  Response: $response" -ForegroundColor Gray
