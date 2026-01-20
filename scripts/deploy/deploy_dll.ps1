# Deploy new DLL by renaming old one
$oldDll = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"
$newDll = "D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll"
$backupDll = "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll.old"

try {
    if (Test-Path $oldDll) {
        Rename-Item $oldDll $backupDll -Force -ErrorAction Stop
        Write-Host "Old DLL renamed to .old" -ForegroundColor Yellow
    }
    
    Copy-Item $newDll $oldDll -Force -ErrorAction Stop
    Write-Host "SUCCESS: New DLL deployed!" -ForegroundColor Green
    Write-Host "Next: Start Revit, open project, start MCP server, then test!" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
