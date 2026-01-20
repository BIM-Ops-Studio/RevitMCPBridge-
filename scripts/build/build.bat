@echo off
echo Building RevitMCPBridge2026...

set MSBUILD="C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"

REM Restore packages
dotnet restore

REM Build project
%MSBUILD% RevitMCPBridge2026.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:minimal

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo.
    echo Next steps:
    echo 1. Copy bin\Release\RevitMCPBridge2026.dll to C:\ProgramData\Autodesk\Revit\Addins\2026\
    echo 2. Copy RevitMCPBridge2026.addin to %APPDATA%\Autodesk\Revit\Addins\2026\
    echo 3. Restart Revit 2026
) else (
    echo Build failed!
)

pause