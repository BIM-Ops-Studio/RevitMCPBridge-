@echo off
echo Building RevitMCPBridge2026 with SketchPad...
echo.

REM Find MSBuild
set MSBUILD="C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
if not exist %MSBUILD% (
    set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
)
if not exist %MSBUILD% (
    echo ERROR: MSBuild not found. Please install Visual Studio with .NET Desktop Development workload.
    pause
    exit /b 1
)

cd /d D:\RevitMCPBridge2026

echo Restoring NuGet packages...
dotnet restore RevitMCPBridge2026.csproj

echo.
echo Building Release...
%MSBUILD% RevitMCPBridge2026.csproj /p:Configuration=Release /v:minimal /t:Build

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo BUILD SUCCEEDED!
echo.
echo DLL Location: D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll
echo.
echo To use, restart Revit to load the updated add-in.
echo Look for "Sketch Pad" and "Floor Plan Tracer" buttons in the MCP Bridge ribbon tab.
echo.
pause
