@echo off
echo ================================================
echo Building Revit MCP Bridge 2026 - Phase 1
echo ================================================
echo.

cd /d D:\RevitMCPBridge2026

REM Check if dotnet is available
where dotnet >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: dotnet CLI not found!
    echo Please install .NET 8 SDK from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

echo Cleaning previous build...
if exist bin rd /s /q bin
if exist obj rd /s /q obj
echo.

echo Restoring NuGet packages...
dotnet restore RevitMCPBridge.csproj
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to restore packages
    pause
    exit /b 1
)
echo.

echo Building project...
dotnet build RevitMCPBridge.csproj --configuration Release --no-restore
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo ================================================
echo Build successful!
echo ================================================
echo.

REM Find the DLL
set DLL_PATH=bin\Release\net8.0-windows\RevitMCPBridge2026.dll
if not exist "%DLL_PATH%" (
    echo ERROR: DLL not found at %DLL_PATH%
    dir bin\Release /s
    pause
    exit /b 1
)

echo Deploying add-in...
echo.

REM Deploy to Revit add-ins folder
set ADDIN_FOLDER=%APPDATA%\Autodesk\Revit\Addins\2026
if not exist "%ADDIN_FOLDER%" mkdir "%ADDIN_FOLDER%"

echo Copying DLL...
copy /Y "%DLL_PATH%" "%ADDIN_FOLDER%\RevitMCPBridge2026.dll"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy DLL
    pause
    exit /b 1
)

echo Copying .addin manifest...
copy /Y "RevitMCPBridge2026.addin" "%ADDIN_FOLDER%\RevitMCPBridge2026.addin"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy .addin file
    pause
    exit /b 1
)

echo.
echo ================================================
echo Deployment complete!
echo ================================================
echo.
echo Files deployed to:
echo %ADDIN_FOLDER%
echo.
echo Next steps:
echo 1. Close Revit if it's running
echo 2. Start Revit 2026
echo 3. Look for "MCP Bridge" tab in the ribbon
echo 4. Click "Start Server" to enable MCP communication
echo.

pause
