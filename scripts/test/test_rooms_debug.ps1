# Debug script to test different room queries

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

$pipeName = "RevitMCPBridge2026"

Write-Host "`n=== Room Query Debug ===" -ForegroundColor Cyan

# Test 1: getRooms (with Area > 0 filter)
Write-Host "`n[1] Testing getRooms (has Area > 0 filter)..." -ForegroundColor Yellow
$result1 = Send-RevitCommand -PipeName $pipeName -Method "getRooms" -Params @{}
if ($result1.success) {
    Write-Host "  Success: $($result1.result.roomCount) rooms" -ForegroundColor Green
    if ($result1.result.roomCount -gt 0) {
        Write-Host "  First room: $($result1.result.rooms[0].number) - $($result1.result.rooms[0].name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  Failed: $($result1.error)" -ForegroundColor Red
}

# Test 2: getElements with Rooms category
Write-Host "`n[2] Testing getElements (category: Rooms)..." -ForegroundColor Yellow
$result2 = Send-RevitCommand -PipeName $pipeName -Method "getElements" -Params @{ category = "Rooms" }
if ($result2.success) {
    Write-Host "  Success: $($result2.result.elements.Count) rooms" -ForegroundColor Green
    if ($result2.result.elements.Count -gt 0) {
        Write-Host "  First room ID: $($result2.result.elements[0].elementId)" -ForegroundColor Gray
    }
} else {
    Write-Host "  Failed: $($result2.error)" -ForegroundColor Red
}

# Test 3: Full response dump
Write-Host "`n[3] Full getRooms response:" -ForegroundColor Yellow
Write-Host ($result1 | ConvertTo-Json -Depth 5) -ForegroundColor Gray

Write-Host "`n=====================`n" -ForegroundColor Cyan
