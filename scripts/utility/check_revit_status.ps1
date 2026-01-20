# Quick Revit and MCP Bridge Status Check

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Revit & MCP Bridge Status Check" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check 1: Is Revit running?
Write-Host "[1/4] Checking if Revit is running..." -ForegroundColor Yellow
$revitProcess = Get-Process -Name "Revit" -ErrorAction SilentlyContinue

if ($revitProcess) {
    Write-Host "  ✅ Revit is running (PID: $($revitProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "  ❌ Revit is NOT running!" -ForegroundColor Red
    Write-Host "     Please start Revit 2026 and open your project." -ForegroundColor Yellow
    exit 1
}

# Check 2: Is the add-in manifest present?
Write-Host "`n[2/4] Checking add-in manifest..." -ForegroundColor Yellow
$addinPath = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin"

if (Test-Path $addinPath) {
    Write-Host "  ✅ Add-in manifest found" -ForegroundColor Green
    Write-Host "     $addinPath" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Add-in manifest NOT found!" -ForegroundColor Red
    Write-Host "     Expected: $addinPath" -ForegroundColor Yellow
}

# Check 3: Is the DLL present?
Write-Host "`n[3/4] Checking DLL..." -ForegroundColor Yellow
$dllPath = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"

if (Test-Path $dllPath) {
    $dll = Get-Item $dllPath
    Write-Host "  ✅ DLL found" -ForegroundColor Green
    Write-Host "     Size: $([math]::Round($dll.Length / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "     Modified: $($dll.LastWriteTime)" -ForegroundColor Gray
} else {
    Write-Host "  ❌ DLL NOT found!" -ForegroundColor Red
}

# Check 4: Try to connect to MCP pipe
Write-Host "`n[4/4] Testing MCP pipe connection..." -ForegroundColor Yellow

try {
    $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipeClient.Connect(3000)

    if ($pipeClient.IsConnected) {
        Write-Host "  ✅ MCP Server is responding!" -ForegroundColor Green
        $pipeClient.Close()
    }
} catch {
    Write-Host "  ❌ MCP Server NOT responding!" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray

    Write-Host "`n  Possible causes:" -ForegroundColor Yellow
    Write-Host "    1. Add-in didn't load in Revit" -ForegroundColor Yellow
    Write-Host "    2. Server failed to start" -ForegroundColor Yellow
    Write-Host "    3. Wrong Revit version (needs 2026)" -ForegroundColor Yellow
}

# Check log file
Write-Host "`n[BONUS] Checking today's log file..." -ForegroundColor Yellow
$logPath = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\Logs\mcp_$(Get-Date -Format 'yyyyMMdd')$(Get-Date -Format 'yyyyMMdd').log"

if (Test-Path $logPath) {
    $log = Get-Item $logPath
    Write-Host "  ✅ Log file found" -ForegroundColor Green
    Write-Host "     Size: $($log.Length) bytes" -ForegroundColor Gray
    Write-Host "     Modified: $($log.LastWriteTime)" -ForegroundColor Gray

    Write-Host "`n  Last 10 log entries:" -ForegroundColor Cyan
    Get-Content $logPath -Tail 10 | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠️  No log file for today" -ForegroundColor Yellow
    Write-Host "     Expected: $logPath" -ForegroundColor Gray
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "If the MCP Server is not responding:" -ForegroundColor Yellow
Write-Host "  1. Check if you see 'MCP Bridge' tab in Revit ribbon" -ForegroundColor White
Write-Host "  2. If not visible, the add-in didn't load:" -ForegroundColor White
Write-Host "     - Check Revit version (must be 2026)" -ForegroundColor Gray
Write-Host "     - Look for error messages in Revit" -ForegroundColor Gray
Write-Host "  3. If visible but server not responding:" -ForegroundColor White
Write-Host "     - Click the 'Start Server' button in MCP Bridge tab" -ForegroundColor Gray
Write-Host "     - Check the log file for errors`n" -ForegroundColor Gray

Write-Host "============================================================`n" -ForegroundColor Cyan
