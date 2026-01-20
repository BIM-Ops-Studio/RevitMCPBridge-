@echo off
echo Building MCP Bridge Tab for Revit 2026 (.NET 8)
echo ===============================================
echo.

cd /d D:\RevitMCPBridge2026

echo Building with dotnet...
dotnet build MCPBridgeTab.csproj -c Release

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo.
    echo Deploying to Revit...
    copy "bin\MCPBridgeTab.dll" "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    echo.
    echo Deployment complete!
    echo.
    echo IMPORTANT: Make sure MCPBridgeTab.addin is in:
    echo C:\Users\%USERNAME%\AppData\Roaming\Autodesk\Revit\Addins\2026\
    echo.
    echo Then restart Revit 2026 to see the MCP Bridge tab.
) else (
    echo.
    echo Build failed!
    echo.
    echo If you don't have .NET 8 SDK installed, you can download it from:
    echo https://dotnet.microsoft.com/download/dotnet/8.0
)

pause