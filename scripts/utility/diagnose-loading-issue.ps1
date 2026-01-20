# PowerShell script to diagnose MCP Bridge loading issue

Write-Host "MCP Bridge Loading Diagnostics" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Check manifest file
$manifestPath = "$env:APPDATA\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin"
Write-Host "1. Checking manifest file..." -ForegroundColor Yellow
if (Test-Path $manifestPath) {
    Write-Host "   [OK] Manifest found at: $manifestPath" -ForegroundColor Green
    Write-Host "   Content:" -ForegroundColor Gray
    Get-Content $manifestPath | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   [ERROR] Manifest not found!" -ForegroundColor Red
}

Write-Host ""

# Check DLL
$dllPath = "$env:APPDATA\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"
Write-Host "2. Checking DLL file..." -ForegroundColor Yellow
if (Test-Path $dllPath) {
    $fileInfo = Get-Item $dllPath
    Write-Host "   [OK] DLL found" -ForegroundColor Green
    Write-Host "   Size: $($fileInfo.Length) bytes" -ForegroundColor Gray
    Write-Host "   Modified: $($fileInfo.LastWriteTime)" -ForegroundColor Gray
    
    # Try to check if it's a .NET assembly
    try {
        Add-Type -Path $dllPath -ErrorAction Stop
        Write-Host "   [OK] DLL loads as .NET assembly" -ForegroundColor Green
    } catch {
        Write-Host "   [WARNING] Cannot load DLL directly (this is normal outside Revit)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [ERROR] DLL not found!" -ForegroundColor Red
}

Write-Host ""

# Check for other MCP Bridge files
Write-Host "3. Checking for conflicting installations..." -ForegroundColor Yellow
$mcpFiles = Get-ChildItem "$env:APPDATA\Autodesk\Revit\Addins\2026" -Filter "*MCP*" | Where-Object { $_.Name -ne "RevitMCPBridge2026.dll" -and $_.Name -ne "RevitMCPBridge2026.addin" }
if ($mcpFiles.Count -gt 0) {
    Write-Host "   [WARNING] Found other MCP-related files:" -ForegroundColor Yellow
    $mcpFiles | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Yellow }
} else {
    Write-Host "   [OK] No conflicting MCP files found" -ForegroundColor Green
}

Write-Host ""

# Suggest solution
Write-Host "4. Suggested Solution:" -ForegroundColor Yellow
Write-Host "   The error 'Could not load type RevitMCPBridge.RevitMCPBridgeApp' usually means:" -ForegroundColor White
Write-Host "   - The DLL was compiled with a different .NET version than expected" -ForegroundColor White
Write-Host "   - There's a namespace/class name mismatch" -ForegroundColor White
Write-Host ""
Write-Host "   Try this fix:" -ForegroundColor Green
Write-Host "   1. Close Revit 2026" -ForegroundColor White
Write-Host "   2. Delete all MCP-related files from the addins folder" -ForegroundColor White
Write-Host "   3. Run 'clean-build.bat' to rebuild fresh" -ForegroundColor White
Write-Host "   4. Restart Revit 2026" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")