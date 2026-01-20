@echo off
echo ========================================
echo MCP Bridge - Clean Installation Fix
echo ========================================
echo.
echo This will clean up all MCP files and do a fresh install.
echo.
echo Press Ctrl+C to cancel, or
pause

set ADDIN_DIR=%APPDATA%\Autodesk\Revit\Addins\2026

echo.
echo Step 1: Backing up and removing old MCP files...
if not exist "%ADDIN_DIR%\MCP_Backup" mkdir "%ADDIN_DIR%\MCP_Backup"

REM Move all MCP-related files to backup
move "%ADDIN_DIR%\*MCP*.addin*" "%ADDIN_DIR%\MCP_Backup\" 2>nul
move "%ADDIN_DIR%\*MCP*.dll*" "%ADDIN_DIR%\MCP_Backup\" 2>nul
move "%ADDIN_DIR%\revit-mcp.*" "%ADDIN_DIR%\MCP_Backup\" 2>nul

echo [OK] Old files backed up

echo.
echo Step 2: Creating fresh manifest with .NET 8 runtime config...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>MCP Bridge^</Name^>
echo     ^<Assembly^>RevitMCPBridge2026.dll^</Assembly^>
echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^>
echo     ^<ClientId^>FA7C6E4A-E3D2-4B87-9D72-A91D7A5C4F82^</ClientId^>
echo     ^<VendorId^>MCPBridge^</VendorId^>
echo     ^<VendorDescription^>Model Context Protocol Bridge for Revit 2026^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%ADDIN_DIR%\RevitMCPBridge2026.addin"

echo [OK] Manifest created

echo.
echo Step 3: Creating runtime config for .NET 8...
(
echo {
echo   "runtimeOptions": {
echo     "tfm": "net8.0",
echo     "framework": {
echo       "name": "Microsoft.NETCore.App",
echo       "version": "8.0.0"
echo     }
echo   }
echo }
) > "%ADDIN_DIR%\RevitMCPBridge2026.runtimeconfig.json"

echo [OK] Runtime config created

echo.
echo Step 4: Rebuilding and deploying DLL...
cd /d D:\RevitMCPBridge2026

REM Clean build
if exist obj rd /s /q obj
if exist bin rd /s /q bin

dotnet build RevitMCPBridge.csproj --configuration Release --verbosity quiet

if exist "bin\Release\net8.0-windows\RevitMCPBridge2026.dll" (
    copy /Y "bin\Release\net8.0-windows\RevitMCPBridge2026.dll" "%ADDIN_DIR%\" >nul
    echo [OK] DLL deployed
    
    REM Also copy dependencies if they exist
    if exist "bin\Release\net8.0-windows\*.dll" (
        copy /Y "bin\Release\net8.0-windows\Serilog*.dll" "%ADDIN_DIR%\" >nul 2>nul
        copy /Y "bin\Release\net8.0-windows\Newtonsoft.Json.dll" "%ADDIN_DIR%\" >nul 2>nul
    )
) else (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo CLEAN INSTALLATION COMPLETE!
echo ========================================
echo.
echo The MCP Bridge has been cleanly installed.
echo.
echo Next steps:
echo 1. Close Revit 2026 if it's running
echo 2. Start Revit 2026
echo 3. Look for "MCP Bridge" in the ribbon tabs
echo.
echo If you still see errors, check:
echo - Windows Event Viewer for .NET errors
echo - Revit journal file for loading errors
echo.
pause