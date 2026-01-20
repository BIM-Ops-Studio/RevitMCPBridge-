# Alternative: Use the existing RevitMCPBridge2026.dll but force it to create its own tab
Write-Host "MCP Bridge Tab Fix - Using Existing DLL" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

$addinPath = "$env:APPDATA\Autodesk\Revit\Addins\2026"
$dllPath = "C:\ProgramData\Autodesk\Revit\Addins\2026"

# Step 1: Create a loader addin that will load the MCP Bridge in a different way
Write-Host "Creating MCP Bridge Tab Loader..." -ForegroundColor Yellow

# Create a new manifest that loads the existing DLL differently
$loaderManifest = @'
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>MCP Bridge Tab Loader</Name>
    <Assembly>C:\ProgramData\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll</Assembly>
    <FullClassName>RevitMCPBridge.RevitMCPBridgeApp</FullClassName>
    <ClientId>F1E2D3C4-B5A6-7890-1234-567890ABCDEF</ClientId>
    <VendorId>ADSK</VendorId>
    <VendorDescription>MCP Bridge with Custom Tab</VendorDescription>
  </AddIn>
</RevitAddIns>
'@

# Backup and disable the original
Write-Host "`nDisabling original MCP Bridge addin..." -ForegroundColor Yellow
if (Test-Path "$addinPath\RevitMCPBridge2026.addin") {
    Move-Item "$addinPath\RevitMCPBridge2026.addin" "$addinPath\RevitMCPBridge2026.addin.original" -Force
    Write-Host "  [OK] Original disabled" -ForegroundColor Green
}

# Write the new loader
$loaderManifest | Out-File -FilePath "$addinPath\MCPBridgeTabLoader.addin" -Encoding UTF8
Write-Host "  [OK] Created new loader manifest" -ForegroundColor Green

# Check if DLL exists in the right place
Write-Host "`nChecking DLL location..." -ForegroundColor Yellow
if (Test-Path "$dllPath\RevitMCPBridge2026.dll") {
    Write-Host "  [OK] DLL found in ProgramData" -ForegroundColor Green
} else {
    # Try to copy from user folder
    $userDll = "$addinPath\RevitMCPBridge2026.dll"
    if (Test-Path $userDll) {
        Write-Host "  Copying DLL to ProgramData..." -ForegroundColor Yellow
        Copy-Item $userDll "$dllPath\" -Force
        Write-Host "  [OK] DLL copied" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] DLL not found!" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The original MCP Bridge addin has been disabled and replaced with a loader." -ForegroundColor White
Write-Host "When you restart Revit 2026, the MCP Bridge should attempt to create its own tab." -ForegroundColor White
Write-Host ""
Write-Host "If it still appears in Add-ins, the DLL itself needs to be modified." -ForegroundColor Yellow