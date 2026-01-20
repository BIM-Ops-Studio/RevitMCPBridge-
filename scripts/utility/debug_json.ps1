# Debug JSON parsing
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

$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getRooms" -Params @{}

Write-Host "`n=== RAW RESULT ===" -ForegroundColor Cyan
Write-Host "Type: $($result.GetType().FullName)"
Write-Host "Success: $($result.success)"
Write-Host "`n=== RESULT OBJECT ===" -ForegroundColor Cyan
Write-Host ($result | ConvertTo-Json -Depth 5)

Write-Host "`n=== PROPERTY ACCESS TESTS ===" -ForegroundColor Cyan
Write-Host "result.result type: $($result.result.GetType().FullName)"
Write-Host "result.result.roomCount: $($result.result.roomCount)"
Write-Host "result.result.rooms type: $($result.result.rooms.GetType().FullName)"
Write-Host "result.result.rooms.Count: $($result.result.rooms.Count)"
Write-Host "result.result.rooms[0].number: $($result.result.rooms[0].number)"
