@echo off
echo Building Minimal MCP Bridge...
echo =============================

cd /d D:\RevitMCPBridge2026

REM Delete old build artifacts
if exist obj rd /s /q obj
if exist bin rd /s /q bin

REM Build just the minimal file
"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" ^
    /target:library ^
    /out:MinimalMCPBridge.dll ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" ^
    MinimalMCPBridge.cs

if exist MinimalMCPBridge.dll (
    echo.
    echo Build successful!
    echo.
    echo Deploying...
    copy /Y MinimalMCPBridge.dll "%APPDATA%\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"
    echo.
    echo Deployment complete!
    echo Restart Revit 2026 to test.
) else (
    echo.
    echo Build failed!
    echo.
    echo Trying with dotnet...
    dotnet build RevitMCPBridge.csproj --configuration Release
)

pause