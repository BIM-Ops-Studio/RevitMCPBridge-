@echo off
set ADDIN_FOLDER=%APPDATA%\Autodesk\Revit\Addins\2026
if not exist "%ADDIN_FOLDER%" mkdir "%ADDIN_FOLDER%"

echo Deploying DLL...
copy /Y "D:\RevitMCPBridge2026\bin\Release\net8.0-windows\RevitMCPBridge2026.dll" "%ADDIN_FOLDER%\RevitMCPBridge2026.dll"

echo Deploying .addin file...
copy /Y "D:\RevitMCPBridge2026\RevitMCPBridge2026.addin" "%ADDIN_FOLDER%\RevitMCPBridge2026.addin"

echo.
echo Deployment complete!
echo Files deployed to: %ADDIN_FOLDER%
