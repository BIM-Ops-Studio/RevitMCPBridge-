# Deep Investigation - Find ALL possible ways to control room boundaries
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

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DEEP INVESTIGATION - All Room Boundary Parameters" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Get ALL parameters from a hallway wall
Write-Host "[1/3] Getting ALL wall parameters..." -ForegroundColor Yellow
$wallParams = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getParameters" -Params @{
    elementId = "1307543"
}

if ($wallParams.success) {
    Write-Host "✅ Found $($wallParams.parameters.Count) wall parameters" -ForegroundColor Green

    # Look for boundary-related parameters
    $boundaryParams = $wallParams.parameters | Where-Object {
        $_.name -like "*boundary*" -or
        $_.name -like "*offset*" -or
        $_.name -like "*location*" -or
        $_.name -like "*room*"
    }

    if ($boundaryParams) {
        Write-Host "`n  Boundary-related parameters:" -ForegroundColor Cyan
        $boundaryParams | ForEach-Object {
            Write-Host "    • $($_.name): $($_.value)" -ForegroundColor White
        }
    }
}

# Get ALL parameters from the room
Write-Host "`n[2/3] Getting ALL room parameters..." -ForegroundColor Yellow
$roomParams = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getParameters" -Params @{
    elementId = "1314059"
}

if ($roomParams.success) {
    Write-Host "✅ Found $($roomParams.parameters.Count) room parameters" -ForegroundColor Green

    # Look for boundary-related parameters
    $roomBoundaryParams = $roomParams.parameters | Where-Object {
        $_.name -like "*boundary*" -or
        $_.name -like "*offset*" -or
        $_.name -like "*calculation*" -or
        $_.name -like "*base*"
    }

    if ($roomBoundaryParams) {
        Write-Host "`n  Boundary-related parameters:" -ForegroundColor Cyan
        $roomBoundaryParams | ForEach-Object {
            Write-Host "    • $($_.name): $($_.value)" -ForegroundColor White
        }
    }
}

Write-Host "`n[3/3] Checking for Room Calculation Point parameter..." -ForegroundColor Yellow
# This is a special parameter that might control room boundary calculation

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Saving full parameter lists for analysis..." -ForegroundColor Yellow

# Save full lists
$wallParams | ConvertTo-Json -Depth 5 | Out-File "wall_all_parameters.json"
$roomParams | ConvertTo-Json -Depth 5 | Out-File "room_all_parameters.json"

Write-Host "✅ Saved to:" -ForegroundColor Green
Write-Host "   • wall_all_parameters.json" -ForegroundColor Gray
Write-Host "   • room_all_parameters.json`n" -ForegroundColor Gray

Write-Host "============================================================`n" -ForegroundColor Cyan
