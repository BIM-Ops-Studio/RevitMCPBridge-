# Automatically create filled regions for all offices
function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

Write-Host "Creating filled regions for all offices..." -ForegroundColor Cyan

$result = Send-RevitCommand -Method "createFilledRegionsForAllOffices" -Params @{
    fillPatternName = "Solid fill"
    transparency = 50
    roomNameFilter = "OFFICE"
}

if ($result.success) {
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Created: $($result.successCount) offices" -ForegroundColor White
    Write-Host "Failed: $($result.failCount) offices" -ForegroundColor Yellow
    Write-Host "View: $($result.viewName)" -ForegroundColor Gray
} else {
    Write-Host "ERROR: $($result.error)" -ForegroundColor Red
}
