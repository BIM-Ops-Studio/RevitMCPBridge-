@echo off
echo Compiling Minimal MCP Bridge...
echo ==============================

set CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
set OUTPUT=RevitMCPBridge2026_TabFix.dll

"%CSC%" /target:library /out:%OUTPUT% ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" ^
    src\MCPBridgeMinimal.cs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Compilation successful!
    echo.
    echo Next steps:
    echo 1. Copy %OUTPUT% to C:\ProgramData\Autodesk\Revit\Addins\2026\
    echo 2. Create a new .addin file pointing to this DLL
    echo 3. Disable the old RevitMCPBridge2026.addin
    echo 4. Restart Revit
) else (
    echo.
    echo Compilation failed!
)

pause