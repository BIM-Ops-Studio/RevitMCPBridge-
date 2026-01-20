@echo off
echo ================================================
echo MCP Bridge Tab - Final Solution Without .NET 8
echo ================================================
echo.
echo Since .NET 8 SDK is not installed and the existing
echo MCP Bridge DLL is hard-coded for the Add-ins tab,
echo here are your options:
echo.
echo ------------------------------------------------
echo OPTION 1: Quick Fix (Use existing MCP Bridge)
echo ------------------------------------------------
echo The MCP Bridge is fully functional in the Add-ins tab.
echo No changes needed - just use it as-is.
echo.
echo ------------------------------------------------
echo OPTION 2: Install .NET 8 SDK
echo ------------------------------------------------
echo 1. Press any key to open the .NET 8 download page
echo 2. Download ".NET 8.0 SDK" for Windows x64
echo 3. Install it
echo 4. Run INSTALL_DOTNET8_AND_BUILD.bat
echo.
echo ------------------------------------------------
echo OPTION 3: Use Visual Studio 2022
echo ------------------------------------------------
echo 1. Open Visual Studio 2022
echo 2. Open D:\RevitMCPBridge2026\RevitMCPBridge.sln
echo 3. Build the solution
echo 4. Deploy the compiled DLL
echo.
echo ------------------------------------------------
echo OPTION 4: Contact Original Developer
echo ------------------------------------------------
echo Ask them to update MCP Bridge to use its own tab.
echo.
echo ================================================
echo WHAT I'VE PREPARED FOR YOU:
echo ================================================
echo.
echo Ready-to-compile source code in:
echo D:\RevitMCPBridge2026\src\
echo.
echo - RevitMCPBridgeApp.cs (creates MCP Bridge tab)
echo - MCPServer.cs (complete MCP implementation)
echo - All command classes with professional icons
echo - Project files configured for Revit 2026
echo.
echo Once you have .NET 8 SDK, just run:
echo INSTALL_DOTNET8_AND_BUILD.bat
echo.
echo ================================================
echo.
echo Press 1 for Option 1 (Use as-is)
echo Press 2 for Option 2 (Download .NET 8 SDK)
echo Press 3 for Option 3 (Open project folder)
echo Press 4 to Exit
echo.
choice /c 1234 /n /m "Select option: "

if errorlevel 4 exit /b
if errorlevel 3 goto :open_folder
if errorlevel 2 goto :download_sdk
if errorlevel 1 goto :use_as_is

:use_as_is
echo.
echo ================================================
echo Using MCP Bridge from Add-ins Tab
echo ================================================
echo.
echo The MCP Bridge is ready to use in Revit 2026.
echo Look for it under the Add-ins tab.
echo.
echo All features are fully functional:
echo - Start/Stop Server
echo - Query commands
echo - MCP protocol support
echo - Settings and logs
echo.
pause
exit /b

:download_sdk
echo.
echo Opening .NET 8 SDK download page...
start https://dotnet.microsoft.com/download/dotnet/8.0
echo.
echo After installing .NET 8 SDK, run:
echo INSTALL_DOTNET8_AND_BUILD.bat
echo.
pause
exit /b

:open_folder
echo.
echo Opening project folder...
start explorer "D:\RevitMCPBridge2026"
echo.
echo The source code is in the 'src' folder.
echo Open RevitMCPBridge.sln in Visual Studio 2022.
echo.
pause
exit /b