@echo off
echo Building RevitMCPBridge2026...

"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" ^
  D:\RevitMCPBridge2026\RevitMCPBridge2026.csproj ^
  /p:Configuration=Release ^
  /v:minimal

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo Build successful! Deploying...

copy /Y ^
  D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll ^
  "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge_v2.dll"

if %errorlevel% neq 0 (
    echo Deploy failed!
    exit /b %errorlevel%
)

echo Deploy successful! Checking file...
dir "C:\Users\rick\AppData\Roaming\Autodesk\Revit\Addins\2026\RevitMCPBridge_v2.dll"

echo.
echo Build and deploy complete!
echo Please restart Revit for changes to take effect.
