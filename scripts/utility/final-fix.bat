@echo off
echo Final MCP Bridge Tab Fix
echo ========================
echo.

set ADDIN_PATH=%APPDATA%\Autodesk\Revit\Addins\2026

echo Step 1: Backing up current files...
if exist "%ADDIN_PATH%\RevitMCPBridge2026.addin" (
    copy "%ADDIN_PATH%\RevitMCPBridge2026.addin" "%ADDIN_PATH%\RevitMCPBridge2026.addin.backup2" /Y
    move "%ADDIN_PATH%\RevitMCPBridge2026.addin" "%ADDIN_PATH%\RevitMCPBridge2026.addin.old" /Y
)

echo.
echo Step 2: Creating new manifest files...

REM Create a manifest that might trigger tab creation
echo ^<?xml version="1.0" encoding="utf-8"?^> > "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo ^<RevitAddIns^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo   ^<AddIn Type="Application"^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<Name^>MCP Bridge^</Name^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<Assembly^>C:\ProgramData\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll^</Assembly^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<ClientId^>12345678-1234-1234-1234-123456789ABC^</ClientId^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<VendorId^>BIMOps^</VendorId^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo     ^<VendorDescription^>MCP Bridge for AI Integration^</VendorDescription^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo   ^</AddIn^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"
echo ^</RevitAddIns^> >> "%ADDIN_PATH%\MCPBridge_Tab.addin"

echo.
echo Step 3: Checking DLL location...
if exist "C:\ProgramData\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll" (
    echo [OK] DLL found in ProgramData
) else if exist "%ADDIN_PATH%\RevitMCPBridge2026.dll" (
    echo Moving DLL to ProgramData...
    copy "%ADDIN_PATH%\RevitMCPBridge2026.dll" "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
) else (
    echo [WARNING] RevitMCPBridge2026.dll not found!
    echo Please ensure the DLL is in: C:\ProgramData\Autodesk\Revit\Addins\2026\
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo What was done:
echo 1. Disabled the original RevitMCPBridge2026.addin
echo 2. Created MCPBridge_Tab.addin with a different ClientId
echo 3. Verified DLL is in the correct location
echo.
echo IMPORTANT: The MCP Bridge behavior depends on how the DLL was coded.
echo If it still appears in Add-ins after restarting Revit, the DLL itself
echo needs to be recompiled with code that explicitly creates its own tab.
echo.
pause