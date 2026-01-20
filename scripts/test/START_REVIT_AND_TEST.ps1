# Simple Start Revit and Test
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Start Revit 2026 and Test Room Boundary Solution" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Start Revit 2026" -ForegroundColor White
Write-Host "2. Open your project: AVENTURA ECO OFFICES - OPTION-2" -ForegroundColor White
Write-Host "3. Open the Level 7 floor plan view" -ForegroundColor White
Write-Host "4. Come back here and press Enter`n" -ForegroundColor White

Read-Host "Press Enter when ready"

Write-Host "`nChecking if Revit is running..." -ForegroundColor Yellow
$revit = Get-Process -Name "Revit" -ErrorAction SilentlyContinue

if (-not $revit) {
    Write-Host "❌ Revit is not running!" -ForegroundColor Red
    Write-Host "   Please start Revit and run this script again.`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Revit is running (PID: $($revit.Id))" -ForegroundColor Green

Write-Host "`nTesting MCP connection..." -ForegroundColor Yellow

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

$testResult = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "getProjectInfo" -Params @{}

if ($testResult.success) {
    Write-Host "✅ MCP Server connected!" -ForegroundColor Green
    Write-Host "   Project: $($testResult.projectName)" -ForegroundColor Gray
} else {
    Write-Host "❌ MCP Server not responding!" -ForegroundColor Red
    Write-Host "   Error: $($testResult.error)" -ForegroundColor Gray
    Write-Host "`n   Possible issues:" -ForegroundColor Yellow
    Write-Host "   1. The add-in didn't load (check Revit ribbon for 'MCP Bridge' tab)" -ForegroundColor White
    Write-Host "   2. The project isn't open yet" -ForegroundColor White
    Write-Host "   3. There's an error in the new code`n" -ForegroundColor White

    # Check log file
    $today = Get-Date -Format 'yyyyMMdd'
    $logPath = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\Logs\mcp_$today.log"

    if (Test-Path $logPath) {
        Write-Host "`n   Recent log entries:" -ForegroundColor Cyan
        Get-Content $logPath -Tail 20 | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Gray
        }
    }

    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "CREATING ROOM SEPARATION LINES FOR OFFICE 40" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  • Identify hallway walls for Office 40" -ForegroundColor White
Write-Host "  • Create room separation lines offset 0.5 ft toward office" -ForegroundColor White
Write-Host "  • Make the room boundary larger (away from hallway)`n" -ForegroundColor White

$result = Send-RevitCommand -PipeName "RevitMCPBridge2026" -Method "createOffsetRoomBoundaries" -Params @{
    roomId = "1314059"
    hallwayOffset = 0.5
    createForDemising = $false
}

if ($result.success) {
    Write-Host "✅ SUCCESS! Room separation lines created!" -ForegroundColor Green
    Write-Host "`nResults:" -ForegroundColor Cyan
    Write-Host "  Room: $($result.roomNumber) - $($result.roomName)" -ForegroundColor White
    Write-Host "  Created $($result.createdLineCount) separation lines" -ForegroundColor White

    if ($result.separationLines) {
        Write-Host "`n  Lines created:" -ForegroundColor Yellow
        $result.separationLines | ForEach-Object {
            Write-Host "    • Wall $($_.wallId): $($_.wallType)" -ForegroundColor Gray
            Write-Host "      Offset: $($_.offsetDistance) ft, Length: $([math]::Round($_.length, 1)) ft" -ForegroundColor DarkGray
        }
    }

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "CHECK OFFICE 40 IN REVIT NOW!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "`nWhat to look for:" -ForegroundColor Yellow
    Write-Host "  1. Magenta dashed lines = Room separation lines" -ForegroundColor White
    Write-Host "  2. Room area should have INCREASED" -ForegroundColor White
    Write-Host "  3. Boundary is now offset from hallway walls" -ForegroundColor White
    Write-Host "  4. Click on Office 40 to see the new area`n" -ForegroundColor White

} else {
    Write-Host "❌ FAILED: $($result.error)" -ForegroundColor Red
    if ($result.stackTrace) {
        Write-Host "`nStack Trace:" -ForegroundColor Yellow
        Write-Host $result.stackTrace -ForegroundColor Gray
    }
}

Write-Host "`n============================================================`n" -ForegroundColor Cyan
