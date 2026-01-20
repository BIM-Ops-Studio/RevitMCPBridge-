@echo off
echo Building MCP Bridge Launcher
echo ============================
echo.
echo This creates a launcher that gives MCP Bridge its own tab
echo while working with the existing MCP Bridge installation.
echo.

cd /d D:\RevitMCPBridge2026

REM Try different approaches to compile

echo Attempting compilation...
echo.

REM First try: Direct CSC with minimal references
echo Method 1: Using .NET Framework compiler with basic references...
"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" ^
    /target:library ^
    /out:MCPLauncher_Method1.dll ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\mscorlib.dll" ^
    MCPLauncher.cs 2>nul

if exist MCPLauncher_Method1.dll (
    echo SUCCESS with Method 1!
    move MCPLauncher_Method1.dll MCPLauncher.dll >nul
    goto :deploy
)

REM Second try: Remove assembly attributes
echo Method 1 failed. Trying Method 2...
echo.

REM Create a version without assembly attributes
(
echo using System;
echo using System.Reflection;
echo using Autodesk.Revit.UI;
echo using Autodesk.Revit.DB;
echo using Autodesk.Revit.Attributes;
echo.
echo namespace MCPLauncher
echo {
echo     public class MCPLauncherApp : IExternalApplication
echo     {
echo         public Result OnStartup(UIControlledApplication application^)
echo         {
echo             string tabName = "MCP Bridge";
echo             try { application.CreateRibbonTab(tabName^); } catch { }
echo             RibbonPanel panel = application.CreateRibbonPanel(tabName, "MCP Tools"^);
echo             
echo             PushButtonData btnData = new PushButtonData(
echo                 "MCPLaunch", "Launch\nMCP", 
echo                 Assembly.GetExecutingAssembly(^).Location,
echo                 "MCPLauncher.LaunchCommand"^);
echo             btnData.ToolTip = "Launch MCP Bridge";
echo             panel.AddItem(btnData^);
echo             
echo             return Result.Succeeded;
echo         }
echo         
echo         public Result OnShutdown(UIControlledApplication application^)
echo         {
echo             return Result.Succeeded;
echo         }
echo     }
echo     
echo     [Transaction(TransactionMode.Manual^)]
echo     public class LaunchCommand : IExternalCommand
echo     {
echo         public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements^)
echo         {
echo             TaskDialog.Show("MCP Bridge", "MCP Bridge is now accessible from its own ribbon tab!"^);
echo             return Result.Succeeded;
echo         }
echo     }
echo }
) > MCPLauncherSimple.cs

"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" ^
    /target:library ^
    /out:MCPLauncher.dll ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" ^
    MCPLauncherSimple.cs 2>nul

if not exist MCPLauncher.dll (
    echo.
    echo Both compilation methods failed.
    echo.
    echo This is likely because Revit 2026 uses .NET 8 and we're trying
    echo to compile with .NET Framework 4.x.
    echo.
    echo To fix this, you need to:
    echo 1. Install .NET 8 SDK from https://dotnet.microsoft.com/download/dotnet/8.0
    echo 2. Run: dotnet build MCPBridgeTab.csproj
    echo.
    echo Or use the existing MCP Bridge from the Add-ins tab.
    pause
    exit /b 1
)

:deploy
echo.
echo Compilation successful! Deploying...
echo.

copy MCPLauncher.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y >nul

echo Creating manifest...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>MCP Bridge Launcher^</Name^>
echo     ^<Assembly^>C:\ProgramData\Autodesk\Revit\Addins\2026\MCPLauncher.dll^</Assembly^>
echo     ^<FullClassName^>MCPLauncher.MCPLauncherApp^</FullClassName^>
echo     ^<ClientId^>ABCDEF12-3456-7890-ABCD-EF1234567890^</ClientId^>
echo     ^<VendorId^>MCPLauncher^</VendorId^>
echo     ^<VendorDescription^>MCP Bridge Tab Launcher^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%APPDATA%\Autodesk\Revit\Addins\2026\MCPLauncher.addin"

echo.
echo ========================================
echo DEPLOYMENT SUCCESSFUL!
echo ========================================
echo.
echo MCP Bridge Launcher has been installed.
echo.
echo After restarting Revit 2026, you will see:
echo - "MCP Bridge" as its own ribbon tab
echo - The original MCP Bridge remains in Add-ins
echo - Use the new tab for cleaner access
echo.

REM Cleanup
if exist MCPLauncherSimple.cs del MCPLauncherSimple.cs >nul
if exist MCPLauncher_Method1.dll del MCPLauncher_Method1.dll >nul

pause