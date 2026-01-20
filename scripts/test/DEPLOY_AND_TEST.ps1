# Deploy Updated DLL and Test Filled Region
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Deploy and Test Automated Filled Region" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check if Revit is running
$revit = Get-Process -Name "Revit" -ErrorAction SilentlyContinue

if ($revit) {
    Write-Host "⚠️  WARNING: Revit is currently running!" -ForegroundColor Yellow
    Write-Host "   You must close Revit before deploying the new DLL.`n" -ForegroundColor Yellow

    Write-Host "Steps to complete:" -ForegroundColor Cyan
    Write-Host "  1. Close Revit now" -ForegroundColor White
    Write-Host "  2. Run this script again" -ForegroundColor White
    Write-Host "  3. Restart Revit and open your project" -ForegroundColor White
    Write-Host "  4. Open Level 7 floor plan view" -ForegroundColor White
    Write-Host "  5. Run TEST_FILLED_REGION.ps1`n" -ForegroundColor White

    $response = Read-Host "Do you want to continue anyway? (y/n)"
    if ($response -ne "y") {
        Write-Host "`nExiting. Please close Revit and try again.`n" -ForegroundColor Yellow
        exit 0
    }
}

# Deploy DLL
Write-Host "Deploying new DLL..." -ForegroundColor Yellow

$sourceDll = "bin\Release\RevitMCPBridge2026.dll"
$targetDir = "$env:APPDATA\Autodesk\Revit\Addins\2026"
$targetDll = "$targetDir\RevitMCPBridge2026.dll"

if (-not (Test-Path $sourceDll)) {
    Write-Host "❌ ERROR: DLL not found at $sourceDll" -ForegroundColor Red
    Write-Host "   Run build.ps1 first!`n" -ForegroundColor Yellow
    exit 1
}

try {
    Copy-Item -Path $sourceDll -Destination $targetDll -Force
    Write-Host "✅ DLL deployed successfully!" -ForegroundColor Green
    Write-Host "   Location: $targetDll`n" -ForegroundColor Gray
}
catch {
    Write-Host "❌ ERROR: Failed to deploy DLL" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host "`n   Make sure Revit is closed!`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "WHAT'S NEW IN THIS VERSION" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "✨ INTELLIGENT BOUNDARY OFFSETS:" -ForegroundColor Green
Write-Host "  • EXTERIOR walls → Boundary at exterior face (outside building)" -ForegroundColor Magenta
Write-Host "  • HALLWAY walls → Boundary at hallway face (away from office)" -ForegroundColor Yellow
Write-Host "  • DEMISING walls → Boundary at center (no offset)" -ForegroundColor Cyan
Write-Host "  • Automatic wall classification" -ForegroundColor White
Write-Host "  • Calculates effective usable area`n" -ForegroundColor White

Write-Host "This gives you accurate lease-ready square footage!`n" -ForegroundColor Green

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "1. Start Revit 2026" -ForegroundColor White
Write-Host "2. Open: AVENTURA ECO OFFICES - OPTION-2" -ForegroundColor White
Write-Host "3. Open the Level 7 floor plan view" -ForegroundColor White
Write-Host "4. Run: .\TEST_FILLED_REGION.ps1`n" -ForegroundColor White

Write-Host "The test will now show detailed diagnostics about:" -ForegroundColor Yellow
Write-Host "  • How many boundary loops Office 40 has" -ForegroundColor Gray
Write-Host "  • View type and level elevation" -ForegroundColor Gray
Write-Host "  • Whether the curve loop is closed" -ForegroundColor Gray
Write-Host "  • Each curve's length and coordinates" -ForegroundColor Gray
Write-Host "  • Exact error from Revit API`n" -ForegroundColor Gray

Write-Host "This will help us fix the filled region creation!`n" -ForegroundColor Cyan

Write-Host "============================================================`n" -ForegroundColor Cyan
