@echo off
echo ========================================
echo MCP Bridge Tab - .NET 8 Build Solution
echo ========================================
echo.
echo This script will help you build the MCP Bridge Tab properly.
echo.
echo STEP 1: Check for .NET 8 SDK
echo -----------------------------
dotnet --list-sdks 2>nul | findstr "8.0" >nul
if %errorlevel% equ 0 (
    echo [OK] .NET 8 SDK is installed!
    echo.
    goto :build
)
echo [ERROR] .NET 8 SDK is NOT installed!
echo.
echo Please install it from:
echo https://dotnet.microsoft.com/download/dotnet/8.0
echo.
echo Download the SDK (not just runtime) for Windows x64
echo.
echo After installation, run this script again.
echo.
pause
start https://dotnet.microsoft.com/download/dotnet/8.0
exit /b 1

:build
echo STEP 2: Building MCP Bridge Tab
echo --------------------------------
cd /d D:\RevitMCPBridge2026

echo Restoring NuGet packages...
dotnet restore RevitMCPBridge.csproj

echo.
echo Building project...
dotnet build RevitMCPBridge.csproj --configuration Release

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Build completed!
    echo.
    echo STEP 3: Deploying
    echo -----------------
    
    REM Copy DLL
    copy "bin\Release\net8.0-windows\RevitMCPBridge2026.dll" "%APPDATA%\Autodesk\Revit\Addins\2026\" /Y
    
    REM Create manifest
    (
        echo ^<?xml version="1.0" encoding="utf-8"?^>
        echo ^<RevitAddIns^>
        echo   ^<AddIn Type="Application"^>
        echo     ^<Name^>MCP Bridge^</Name^>
        echo     ^<Assembly^>%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll^</Assembly^>
        echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^>
        echo     ^<ClientId^>12345678-90AB-CDEF-1234-567890ABCDEF^</ClientId^>
        echo     ^<VendorId^>MCPBridge^</VendorId^>
        echo     ^<VendorDescription^>Model Context Protocol Bridge for Revit^</VendorDescription^>
        echo   ^</AddIn^>
        echo ^</RevitAddIns^>
    ) > "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026_New.addin"
    
    echo.
    echo STEP 4: Cleanup old installation
    echo --------------------------------
    if exist "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin" (
        echo Disabling old manifest...
        move "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin" "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin.old" /Y
    )
    
    echo Renaming new manifest...
    move "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026_New.addin" "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.addin" /Y
    
    echo.
    echo ========================================
    echo INSTALLATION COMPLETE!
    echo ========================================
    echo.
    echo The MCP Bridge has been rebuilt and deployed.
    echo.
    echo When you start Revit 2026, you should see:
    echo - "MCP Bridge" as its own ribbon tab (not in Add-ins)
    echo - Professional icons for all commands
    echo - Full MCP functionality
    echo.
    echo If you still see it in Add-ins, check:
    echo 1. All old .addin files are disabled
    echo 2. No duplicate DLLs exist
    echo 3. Revit was fully restarted
    echo.
) else (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo - Missing Revit API references
    echo - Wrong .NET version
    echo - Permission issues
    echo.
)

pause