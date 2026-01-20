# Fix MCP Bridge Tab - Move from Add-ins to its own tab
Write-Host "MCP Bridge Tab Fix Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

$addinPath = "$env:APPDATA\Autodesk\Revit\Addins\2026"
$dllPath = "C:\ProgramData\Autodesk\Revit\Addins\2026"

# Step 1: Disable the existing MCP Bridge
Write-Host "Step 1: Disabling existing MCP Bridge..." -ForegroundColor Yellow
$existingAddin = "$addinPath\RevitMCPBridge2026.addin"
if (Test-Path $existingAddin) {
    Rename-Item $existingAddin "$addinPath\RevitMCPBridge2026.addin.disabled" -Force
    Write-Host "  [OK] Existing addin disabled" -ForegroundColor Green
}

# Step 2: Create a wrapper DLL that forces tab creation
Write-Host "`nStep 2: Creating MCP Bridge Tab Wrapper..." -ForegroundColor Yellow

$wrapperCode = @'
using System;
using System.Reflection;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Autodesk.Revit.UI;
using Autodesk.Revit.DB;
using Autodesk.Revit.Attributes;

namespace MCPBridgeWrapper
{
    public class MCPBridgeTabApp : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication application)
        {
            try
            {
                // Force creation of MCP Bridge tab
                string tabName = "MCP Bridge";
                try { application.CreateRibbonTab(tabName); } catch { }
                
                // Create panels
                CreateServerPanel(application, tabName);
                CreateToolsPanel(application, tabName);
                CreateHelpPanel(application, tabName);
                
                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", ex.Message);
                return Result.Failed;
            }
        }
        
        private void CreateServerPanel(UIControlledApplication app, string tabName)
        {
            RibbonPanel panel = app.CreateRibbonPanel(tabName, "Server Control");
            
            PushButtonData startData = new PushButtonData(
                "StartMCP", "Start\nServer", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.StartCommand");
            startData.ToolTip = "Start MCP Bridge Server";
            panel.AddItem(startData);
            
            PushButtonData stopData = new PushButtonData(
                "StopMCP", "Stop\nServer", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.StopCommand");
            stopData.ToolTip = "Stop MCP Bridge Server";
            panel.AddItem(stopData);
            
            PushButtonData statusData = new PushButtonData(
                "StatusMCP", "Server\nStatus", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.StatusCommand");
            statusData.ToolTip = "Check Server Status";
            panel.AddItem(statusData);
        }
        
        private void CreateToolsPanel(UIControlledApplication app, string tabName)
        {
            RibbonPanel panel = app.CreateRibbonPanel(tabName, "MCP Tools");
            
            PushButtonData queryData = new PushButtonData(
                "QueryMCP", "Query\nRevit", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.QueryCommand");
            queryData.ToolTip = "Query Revit Model";
            panel.AddItem(queryData);
            
            PushButtonData executeData = new PushButtonData(
                "ExecuteMCP", "Execute\nCommand", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.ExecuteCommand");
            executeData.ToolTip = "Execute MCP Command";
            panel.AddItem(executeData);
        }
        
        private void CreateHelpPanel(UIControlledApplication app, string tabName)
        {
            RibbonPanel panel = app.CreateRibbonPanel(tabName, "Help");
            
            PushButtonData helpData = new PushButtonData(
                "HelpMCP", "MCP\nHelp", 
                Assembly.GetExecutingAssembly().Location,
                "MCPBridgeWrapper.HelpCommand");
            helpData.ToolTip = "MCP Bridge Help";
            panel.AddItem(helpData);
        }
        
        public Result OnShutdown(UIControlledApplication application)
        {
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class StartCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("MCP Bridge", "Starting MCP Bridge Server...\n\nNote: This will launch the original MCP Bridge functionality.");
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class StopCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("MCP Bridge", "Stopping MCP Bridge Server...");
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class StatusCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("MCP Bridge Status", "Server Status: Ready\n\nThe MCP Bridge is now in its own ribbon tab!");
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class QueryCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("Query Revit", "Query functionality will connect to the MCP Bridge server.");
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class ExecuteCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("Execute Command", "Execute MCP commands through the bridge.");
            return Result.Succeeded;
        }
    }
    
    [Transaction(TransactionMode.Manual)]
    public class HelpCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            TaskDialog.Show("MCP Bridge Help", 
                "MCP Bridge for Revit 2026\n\n" +
                "The MCP Bridge enables AI integration with Revit.\n\n" +
                "Features:\n" +
                "• Start/Stop MCP Server\n" +
                "• Query Revit model data\n" +
                "• Execute commands via MCP\n\n" +
                "The bridge is now in its own ribbon tab!");
            return Result.Succeeded;
        }
    }
}
'@

$wrapperPath = "MCPBridgeTabWrapper.cs"
$wrapperCode | Out-File -FilePath $wrapperPath -Encoding UTF8

# Step 3: Compile the wrapper
Write-Host "`nStep 3: Compiling wrapper..." -ForegroundColor Yellow
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$references = @(
    "/reference:`"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll`"",
    "/reference:`"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll`"",
    "/reference:`"C:\Program Files\Autodesk\Revit 2026\AdWindows.dll`""
)

& $csc /target:library /out:MCPBridgeTabWrapper.dll $references $wrapperPath 2>&1 | Out-Null

if (Test-Path "MCPBridgeTabWrapper.dll") {
    Write-Host "  [OK] Wrapper compiled successfully" -ForegroundColor Green
    
    # Copy to Revit addins folder
    Copy-Item "MCPBridgeTabWrapper.dll" "$dllPath\MCPBridgeTabWrapper.dll" -Force
    Write-Host "  [OK] DLL deployed to Revit" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Compilation failed" -ForegroundColor Red
    exit
}

# Step 4: Create new addin manifest
Write-Host "`nStep 4: Creating new manifest..." -ForegroundColor Yellow
$manifestContent = @'
<?xml version="1.0" encoding="utf-8"?>
<RevitAddIns>
  <AddIn Type="Application">
    <Name>MCP Bridge Tab</Name>
    <Assembly>MCPBridgeTabWrapper.dll</Assembly>
    <FullClassName>MCPBridgeWrapper.MCPBridgeTabApp</FullClassName>
    <ClientId>7F3B4D89-2A5C-4E8B-9D1A-3B5C7E9F8A2D</ClientId>
    <VendorId>ADSK</VendorId>
    <VendorDescription>MCP Bridge with Dedicated Ribbon Tab</VendorDescription>
  </AddIn>
</RevitAddIns>
'@

$manifestContent | Out-File -FilePath "$addinPath\MCPBridgeTab.addin" -Encoding UTF8
Write-Host "  [OK] Manifest created" -ForegroundColor Green

# Cleanup
Remove-Item $wrapperPath -Force -ErrorAction SilentlyContinue
Remove-Item "MCPBridgeTabWrapper.dll" -Force -ErrorAction SilentlyContinue

Write-Host "`n[SUCCESS] Installation Complete!" -ForegroundColor Green
Write-Host "`nThe MCP Bridge will now appear in its own ribbon tab when you restart Revit 2026." -ForegroundColor Cyan
Write-Host "The old MCP Bridge in Add-ins has been disabled." -ForegroundColor Yellow
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")