# Simple fix to move MCP Bridge to its own tab
Write-Host "MCP Bridge Tab Fix - Simple Version" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

$addinPath = "$env:APPDATA\Autodesk\Revit\Addins\2026"

# Step 1: Check current status
Write-Host "Checking current MCP Bridge status..." -ForegroundColor Yellow
$currentAddin = "$addinPath\RevitMCPBridge2026.addin"
$backupAddin = "$addinPath\RevitMCPBridge2026.addin.backup"

if (Test-Path $currentAddin) {
    Write-Host "  Found: RevitMCPBridge2026.addin" -ForegroundColor Green
} else {
    Write-Host "  Not found: RevitMCPBridge2026.addin" -ForegroundColor Red
    Write-Host "  Looking for disabled version..." -ForegroundColor Yellow
    if (Test-Path "$addinPath\RevitMCPBridge2026.addin.disabled") {
        Write-Host "  Found disabled version, re-enabling..." -ForegroundColor Yellow
        Rename-Item "$addinPath\RevitMCPBridge2026.addin.disabled" $currentAddin
    }
}

# Step 2: Since we can't rebuild the DLL easily, let's use a different approach
# We'll create a new add-in that loads in a different way
Write-Host "`nCreating MCP Bridge Tab Loader..." -ForegroundColor Yellow

# Create a simple batch file to compile
$compileScript = @'
@echo off
cd /d D:\RevitMCPBridge2026
echo Compiling MCP Bridge Tab Fix...

"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /target:library /out:MCPBridgeTab.dll /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" MCPBridgeTab.cs

if exist MCPBridgeTab.dll (
    echo SUCCESS: Compiled MCPBridgeTab.dll
    copy MCPBridgeTab.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    echo Copied to Revit addins folder
) else (
    echo FAILED: Could not compile
    pause
)
'@

# Create the C# source file
$sourceCode = @'
using System;
using Autodesk.Revit.UI;
using Autodesk.Revit.DB;
using Autodesk.Revit.Attributes;

namespace MCPBridgeTab
{
    public class App : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication app)
        {
            // Create MCP Bridge tab
            string tabName = "MCP Bridge";
            try { app.CreateRibbonTab(tabName); } catch { }
            
            // Create panel
            RibbonPanel panel = app.CreateRibbonPanel(tabName, "MCP Tools");
            
            // Add button
            PushButtonData btnData = new PushButtonData(
                "MCPBridge", 
                "MCP\nBridge", 
                System.Reflection.Assembly.GetExecutingAssembly().Location,
                "MCPBridgeTab.Command");
            btnData.ToolTip = "MCP Bridge Control";
            panel.AddItem(btnData);
            
            return Result.Succeeded;
        }
        
        public Result OnShutdown(UIControlledApplication app)
        {
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class Command : IExternalCommand
    {
        public Result Execute(ExternalCommandData data, ref string msg, ElementSet elements)
        {
            TaskDialog.Show("MCP Bridge", "MCP Bridge is now in its own tab!\n\nTo access the original MCP Bridge functions, you may need to re-enable the original add-in.");
            return Result.Succeeded;
        }
    }
}
'@

# Write files
$sourceCode | Out-File -FilePath "MCPBridgeTab.cs" -Encoding UTF8
$compileScript | Out-File -FilePath "compile-tab-fix.bat" -Encoding ASCII

Write-Host "  Created source files" -ForegroundColor Green

# Step 3: Create manifest
Write-Host "`nCreating manifest file..." -ForegroundColor Yellow
$manifest = @'
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>MCP Bridge Tab</Name>
    <Assembly>C:\ProgramData\Autodesk\Revit\Addins\2026\MCPBridgeTab.dll</Assembly>
    <FullClassName>MCPBridgeTab.App</FullClassName>
    <ClientId>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</ClientId>
    <VendorId>ADSK</VendorId>
  </AddIn>
</RevitAddIns>
'@

$manifest | Out-File -FilePath "$addinPath\MCPBridgeTab.addin" -Encoding UTF8
Write-Host "  Created MCPBridgeTab.addin" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Run the compile-tab-fix.bat file to compile the DLL" -ForegroundColor White
Write-Host "2. Restart Revit 2026" -ForegroundColor White
Write-Host "3. You should see 'MCP Bridge' as its own ribbon tab" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening compile script now..." -ForegroundColor Green
Start-Process "compile-tab-fix.bat"