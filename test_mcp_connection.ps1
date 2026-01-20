# Test MCP Connection
$pipeName = "RevitMCPBridge2026"

Write-Host "Testing MCP Connection to Revit..." -ForegroundColor Cyan
Write-Host "Pipe: $pipeName"
Write-Host ""

$request = @{
    method = "getLevels"
    params = @{}
} | ConvertTo-Json

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    Write-Host "Connecting to pipe..." -ForegroundColor Yellow
    $pipe.Connect(10000)  # 10 second timeout
    Write-Host "Connected!" -ForegroundColor Green

    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)

    Write-Host "Sending request: getLevels" -ForegroundColor Yellow
    $writer.WriteLine($request)
    $writer.Flush()

    Write-Host "Reading response..." -ForegroundColor Yellow
    $response = $reader.ReadLine()

    $pipe.Close()

    Write-Host ""
    Write-Host "Response received:" -ForegroundColor Green
    Write-Host $response

    $json = $response | ConvertFrom-Json
    if ($json.success) {
        Write-Host ""
        Write-Host "SUCCESS! MCP is working." -ForegroundColor Green
        Write-Host "Found $($json.levels.Count) levels in the model."
    }
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Is Revit open with a project?"
    Write-Host "2. Is the MCP Bridge add-in loaded? (Check Revit ribbon for MCP Tools)"
    Write-Host "3. Click in the Revit drawing area to activate it"
}
