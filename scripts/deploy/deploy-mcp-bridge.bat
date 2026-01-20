@echo off
echo ========================================
echo Deploying MCP Bridge with Own Ribbon Tab
echo ========================================
echo.

set SOURCE_DLL=D:\RevitMCPBridge2026\bin\Release\net8.0-windows\RevitMCPBridge2026.dll
set TARGET_DIR=%APPDATA%\Autodesk\Revit\Addins\2026

echo Step 1: Checking if DLL was built...
if not exist "%SOURCE_DLL%" (
    echo ERROR: DLL not found at %SOURCE_DLL%
    echo Please build the project first!
    pause
    exit /b 1
)

echo [OK] DLL found
echo.

echo Step 2: Backing up old installation...
if exist "%TARGET_DIR%\RevitMCPBridge2026.dll" (
    move /Y "%TARGET_DIR%\RevitMCPBridge2026.dll" "%TARGET_DIR%\RevitMCPBridge2026.dll.old"
    echo [OK] Backed up old DLL
)

if exist "%TARGET_DIR%\RevitMCPBridge2026.addin" (
    move /Y "%TARGET_DIR%\RevitMCPBridge2026.addin" "%TARGET_DIR%\RevitMCPBridge2026.addin.old"
    echo [OK] Backed up old manifest
)

echo.
echo Step 3: Deploying new DLL...
copy /Y "%SOURCE_DLL%" "%TARGET_DIR%\"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy DLL
    pause
    exit /b 1
)
echo [OK] DLL deployed

echo.
echo Step 4: Creating manifest...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>MCP Bridge^</Name^>
echo     ^<Assembly^>%TARGET_DIR%\RevitMCPBridge2026.dll^</Assembly^>
echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^>
echo     ^<ClientId^>FA7C6E4A-E3D2-4B87-9D72-A91D7A5C4F82^</ClientId^>
echo     ^<VendorId^>MCPBridge^</VendorId^>
echo     ^<VendorDescription^>Model Context Protocol Bridge for Revit 2026^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%TARGET_DIR%\RevitMCPBridge2026.addin"

echo [OK] Manifest created
echo.

echo ========================================
echo DEPLOYMENT SUCCESSFUL!
echo ========================================
echo.
echo The MCP Bridge has been deployed with its own ribbon tab.
echo.
echo IMPORTANT:
echo ----------
echo 1. Close Revit 2026 if it's running
echo 2. Start Revit 2026
echo 3. Look for "MCP Bridge" in the ribbon tabs (not in Add-ins!)
echo.
echo The MCP Bridge tab includes:
echo - Server Control panel (Start/Stop/Status)
echo - MCP Tools panel (Query/Execute/Logs)
echo - Settings panel
echo.
echo All buttons have professional 24x24 icons as requested.
echo.
pause