@echo off
echo Deploying MCP Bridge to Revit 2026...

set SOURCE_DLL=bin\Debug\RevitMCPBridge2026.dll
set SOURCE_ADDIN=RevitMCPBridge2026.addin
set TARGET_DLL_PATH=C:\ProgramData\Autodesk\Revit\Addins\2026
set TARGET_ADDIN_PATH=%APPDATA%\Autodesk\Revit\Addins\2026

REM Check if build exists
if not exist "%SOURCE_DLL%" (
    echo Error: %SOURCE_DLL% not found. Please build the project first.
    pause
    exit /b 1
)

REM Create directories if they don't exist
if not exist "%TARGET_DLL_PATH%" mkdir "%TARGET_DLL_PATH%"
if not exist "%TARGET_ADDIN_PATH%" mkdir "%TARGET_ADDIN_PATH%"

REM Copy files
echo Copying DLL...
copy /Y "%SOURCE_DLL%" "%TARGET_DLL_PATH%\"
copy /Y "bin\Debug\Newtonsoft.Json.dll" "%TARGET_DLL_PATH%\" 2>nul
copy /Y "bin\Debug\Serilog.dll" "%TARGET_DLL_PATH%\" 2>nul
copy /Y "bin\Debug\Serilog.Sinks.File.dll" "%TARGET_DLL_PATH%\" 2>nul

echo Copying manifest...
copy /Y "%SOURCE_ADDIN%" "%TARGET_ADDIN_PATH%\"

echo.
echo Deployment complete!
echo Please restart Revit 2026 to load the MCP Bridge.
echo.
echo The MCP Bridge will appear as its own tab in the Revit ribbon.
pause