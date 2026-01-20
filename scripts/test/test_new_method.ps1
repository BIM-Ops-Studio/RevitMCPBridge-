# Test if getRoomBoundaryWalls method exists
function Send-RevitCommand {
    param([string]$PipeName, [string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", $PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        if (-not $pipeClient.IsConnected) { throw "Failed to connect" }
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        if ([string]::IsNullOrEmpty($response)) { throw "Empty response" }
        return $response | ConvertFrom-Json
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient -and $pipeClient.IsConnected) {
            try { $pipeClient.Close() } catch {}
            try { $pipeClient.Dispose() } catch {}
        }
    }
}

Write-Host "Testing getRoomBoundaryWalls method..." -ForegroundColor Cyan

$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRoomBoundaryWalls" -Params @{ roomId = "1314059" }

if ($result.success) {
    Write-Host "✅ Method exists and works!" -ForegroundColor Green
} else {
    Write-Host "❌ Method not available: $($result.error)" -ForegroundColor Red
    Write-Host "`nYou need to close Revit and redeploy the DLL." -ForegroundColor Yellow
}
