# Simple deployment script for MCP Bridge
$revitAddinsPath = "$env:APPDATA\Autodesk\Revit\Addins\2026"

Write-Host "Deploying MCP Bridge to Revit 2026..." -ForegroundColor Cyan

# Backup existing files
if (Test-Path "$revitAddinsPath\RevitMCPBridge2026.dll") {
    Write-Host "Backing up existing MCP Bridge..." -ForegroundColor Yellow
    Copy-Item "$revitAddinsPath\RevitMCPBridge2026.dll" "$revitAddinsPath\RevitMCPBridge2026.dll.backup" -Force
    Copy-Item "$revitAddinsPath\RevitMCPBridge2026.addin" "$revitAddinsPath\RevitMCPBridge2026.addin.backup" -Force
}

# For now, we'll update just the manifest to move it to its own tab
$addinContent = @'
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>MCP Bridge</Name>
    <Assembly>RevitMCPBridge2026.dll</Assembly>
    <FullClassName>RevitMCPBridge.RevitMCPBridgeApp</FullClassName>
    <ClientId>8B8B6F55-9C7A-4F5E-8D8A-1B2C3D4E5F61</ClientId>
    <VendorId>ADSK</VendorId>
    <VendorDescription>Autodesk Developer Network</VendorDescription>
    <Description>MCP Bridge for Revit 2026 - Enables Claude AI integration with Revit API through Model Context Protocol</Description>
  </AddIn>
</RevitAddIns>
'@

# Write the new manifest
$addinContent | Out-File -FilePath "$revitAddinsPath\RevitMCPBridge2026.addin" -Encoding UTF8

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "The existing MCP Bridge DLL is still in use, but the manifest has been updated." -ForegroundColor Yellow
Write-Host "When you restart Revit, MCP Bridge should appear in its own ribbon tab instead of Add-ins." -ForegroundColor Cyan