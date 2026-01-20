# Direct method test - bypasses registry file check
$pipeName = "RevitMCPBridge2026"

$json = '{"method":"getTextTypes","params":{}}'

Write-Host "Testing getTextTypes directly..." -ForegroundColor Yellow
Write-Host "Request: $json"

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $writer.AutoFlush = $true
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $pipe.Close()

    Write-Host ""
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertFrom-Json | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}
