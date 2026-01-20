@echo off
echo Manual MCP Bridge Tab Compilation
echo =================================
echo.

cd /d D:\RevitMCPBridge2026

echo Attempting compilation with .NET Framework compiler...
echo.

set CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
set REVIT=C:\Program Files\Autodesk\Revit 2026

if not exist "%CSC%" (
    echo ERROR: C# compiler not found at %CSC%
    pause
    exit /b 1
)

echo Using compiler: %CSC%
echo.

"%CSC%" /nologo /target:library /out:MCPBridgeTab.dll /reference:"%REVIT%\RevitAPI.dll" /reference:"%REVIT%\RevitAPIUI.dll" MCPBridgeTab.cs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: MCPBridgeTab.dll created
    echo.
    echo Copying to Revit addins folder...
    copy MCPBridgeTab.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    echo.
    echo Installation complete!
    echo.
    echo IMPORTANT: Restart Revit 2026 to see the MCP Bridge tab.
) else (
    echo.
    echo COMPILATION FAILED
    echo.
    echo Possible issues:
    echo 1. Revit 2026 is not installed in the expected location
    echo 2. .NET Framework 4.8 is not installed
    echo 3. Missing Revit API references
)

echo.
pause