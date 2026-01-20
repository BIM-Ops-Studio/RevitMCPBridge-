# Simple MCP Test with explicit UTF8 encoding (no BOM)
$pipeName = "RevitMCPBridge2026"

Write-Host "Simple MCP Test" -ForegroundColor Cyan

# Create JSON manually to avoid any encoding issues
$json = '{"method":"getLevels","params":{}}'

Write-Host "Request: $json"
Write-Host ""

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(10000)

    # Use UTF8 without BOM
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
    $reader = New-Object System.IO.StreamReader($pipe, $utf8)

    $writer.WriteLine($json)
    $writer.Flush()

    $response = $reader.ReadLine()
    $pipe.Close()

    Write-Host "Response:" -ForegroundColor Green
    Write-Host $response
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
