# Rebuild RevitMCPBridge2026 add-in
Write-Host "Building RevitMCPBridge2026..." -ForegroundColor Cyan

dotnet build RevitMCPBridge2026.csproj -c Release

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Please restart the Revit add-in server to load the updated DLL." -ForegroundColor Yellow
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
}
