@echo off
echo ========================================
echo Clean Build MCP Bridge
echo ========================================
echo.

cd /d D:\RevitMCPBridge2026

echo Step 1: Cleaning old build artifacts...
if exist obj rd /s /q obj
if exist bin rd /s /q bin
echo [OK] Cleaned

echo.
echo Step 2: Building with dotnet...
dotnet clean RevitMCPBridge.csproj
dotnet build RevitMCPBridge.csproj --configuration Release --verbosity minimal

if exist "bin\Release\net8.0-windows\RevitMCPBridge2026.dll" (
    echo.
    echo [OK] Build successful!
    echo.
    
    echo Step 3: Backing up current installation...
    if exist "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll" (
        del /f "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll.old" 2>nul
        move "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll" "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll.old"
    )
    
    echo.
    echo Step 4: Deploying new DLL...
    copy /Y "bin\Release\net8.0-windows\RevitMCPBridge2026.dll" "%APPDATA%\Autodesk\Revit\Addins\2026\"
    
    echo.
    echo ========================================
    echo DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Close and restart Revit 2026 to load the MCP Bridge tab.
) else (
    echo.
    echo [ERROR] Build failed!
)

pause