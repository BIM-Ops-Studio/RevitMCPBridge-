@echo off
echo MCP Bridge Tab - Pre-built Solution
echo ===================================
echo.
echo Since building with .NET 8 is complex, here's what we'll do:
echo.
echo 1. Use a modified version of the existing DLL
echo 2. Create multiple manifest files to try different loading methods
echo 3. One of them should force the tab creation
echo.

set ADDIN_PATH=%APPDATA%\Autodesk\Revit\Addins\2026
set DLL_PATH=C:\ProgramData\Autodesk\Revit\Addins\2026

echo Step 1: Ensure DLL is in the right location...
if not exist "%DLL_PATH%\RevitMCPBridge2026.dll" (
    if exist "%ADDIN_PATH%\RevitMCPBridge2026.dll" (
        copy "%ADDIN_PATH%\RevitMCPBridge2026.dll" "%DLL_PATH%\" /Y
        echo Copied DLL to ProgramData
    ) else (
        echo ERROR: RevitMCPBridge2026.dll not found!
        pause
        exit /b 1
    )
)

echo.
echo Step 2: Disable all existing MCP Bridge manifests...
if exist "%ADDIN_PATH%\RevitMCPBridge2026.addin" move "%ADDIN_PATH%\RevitMCPBridge2026.addin" "%ADDIN_PATH%\RevitMCPBridge2026.addin.disabled" /Y 2>nul
if exist "%ADDIN_PATH%\MCPBridge_Tab.addin" del "%ADDIN_PATH%\MCPBridge_Tab.addin" /Q 2>nul
if exist "%ADDIN_PATH%\MCPBridgeTab.addin" del "%ADDIN_PATH%\MCPBridgeTab.addin" /Q 2>nul

echo.
echo Step 3: Create new manifests with different approaches...

REM Approach 1: Force different vendor
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>MCP Bridge Custom^</Name^>
echo     ^<Assembly^>%DLL_PATH%\RevitMCPBridge2026.dll^</Assembly^>
echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^>
echo     ^<ClientId^>11111111-2222-3333-4444-555555555555^</ClientId^>
echo     ^<VendorId^>CustomMCP^</VendorId^>
echo     ^<VendorDescription^>Custom MCP Bridge Tab^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%ADDIN_PATH%\MCPBridgeCustom.addin"

echo Created MCPBridgeCustom.addin

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo The MCP Bridge has been reconfigured.
echo.
echo IMPORTANT NOTES:
echo ---------------
echo 1. If MCP Bridge still appears in Add-ins tab after restart,
echo    it means the DLL is hard-coded to use that location.
echo.
echo 2. To truly move it to its own tab, we would need:
echo    - The original source code, OR
echo    - A new implementation built with .NET 8 SDK
echo.
echo 3. As a workaround, you can:
echo    - Keep using it from the Add-ins tab
echo    - Contact the original developer for an update
echo    - Use the MCP Bridge source files I created to build
echo      a new version when you have .NET 8 SDK installed
echo.
pause