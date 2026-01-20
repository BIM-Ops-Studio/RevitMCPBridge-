# Fix Office 40 - Use FinishFaceInterior for hallway walls
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
Write-Host "Office 40 - Fix Hallway Wall Boundaries" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "The issue: Wall 'exterior/interior' orientation" -ForegroundColor Yellow
Write-Host "Solution: Try FinishFaceInterior instead of FinishFaceExterior`n" -ForegroundColor Yellow

# Hallway wall IDs from diagnostic
$hallwayWalls = @(1307543, 1308665)

foreach ($wallId in $hallwayWalls) {
    Write-Host "Modifying Wall $wallId to FinishFaceInterior..." -ForegroundColor Cyan

    $result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "modifyWallProperties" -Params @{
        wallId = $wallId.ToString()
        locationLine = "FinishFaceInterior"
        roomBounding = $true
    }

    if ($result.success) {
        Write-Host "  ✅ SUCCESS! Modified: $($result.modified -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $($result.error)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Done! Check Office 40 in Revit" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nIf the boundary still looks wrong, the walls might be" -ForegroundColor Yellow
Write-Host "oriented the opposite way. In that case, we should use" -ForegroundColor Yellow
Write-Host "FinishFaceExterior but flip which walls get which setting.`n" -ForegroundColor Yellow
