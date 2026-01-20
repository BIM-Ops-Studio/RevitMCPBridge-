# Deploy updated DLL to Revit Addins folder
$sourceDll = "D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll"
$targetDll = "$env:APPDATA\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"

Write-Host "Deploying updated DLL..." -ForegroundColor Cyan
Write-Host "Source: $sourceDll" -ForegroundColor Gray
Write-Host "Target: $targetDll" -ForegroundColor Gray
Write-Host ""

if (-Not (Test-Path $sourceDll)) {
    Write-Host "ERROR: Source DLL not found!" -ForegroundColor Red
    Write-Host "Please run .\rebuild.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Copy the DLL
Copy-Item -Path $sourceDll -Destination $targetDll -Force

if ($?) {
    Write-Host "[SUCCESS] DLL deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Close Revit completely"
    Write-Host "2. Reopen Revit and your project"
    Write-Host "3. Start MCP Bridge server in Revit ribbon"
    Write-Host "4. Start HTTP server: python D:\revit-mcp-server\http_server.py"
} else {
    Write-Host "[FAILED] Deployment failed!" -ForegroundColor Red
}
