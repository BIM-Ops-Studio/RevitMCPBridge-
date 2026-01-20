@echo off
echo Building Minimal MCP Bridge Tab
echo ===============================
echo.

cd /d D:\RevitMCPBridge2026

set CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
set REVIT_PATH=C:\Program Files\Autodesk\Revit 2026

echo Compiling MCPBridgeMinimal.cs...
echo.

REM Compile with minimal references
"%CSC%" /nologo /target:library /out:MCPBridgeTab.dll ^
    /reference:"%REVIT_PATH%\RevitAPI.dll" ^
    /reference:"%REVIT_PATH%\RevitAPIUI.dll" ^
    MCPBridgeMinimal.cs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! MCPBridgeTab.dll created
    echo.
    echo Deploying...
    
    REM Copy to both locations
    copy MCPBridgeTab.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    copy MCPBridgeTab.dll "%APPDATA%\Autodesk\Revit\Addins\2026\" /Y
    
    echo.
    echo Creating manifest...
    (
        echo ^<?xml version="1.0" encoding="utf-8"?^>
        echo ^<RevitAddIns^>
        echo   ^<AddIn Type="Application"^>
        echo     ^<Name^>MCP Bridge Tab^</Name^>
        echo     ^<Assembly^>%APPDATA%\Autodesk\Revit\Addins\2026\MCPBridgeTab.dll^</Assembly^>
        echo     ^<FullClassName^>MCPBridgeTab.MCPBridgeTabApp^</FullClassName^>
        echo     ^<ClientId^>BBBBBBBB-2222-3333-4444-CCCCCCCCCCCC^</ClientId^>
        echo     ^<VendorId^>MCPBridgeTab^</VendorId^>
        echo     ^<VendorDescription^>MCP Bridge Ribbon Tab^</VendorDescription^>
        echo   ^</AddIn^>
        echo ^</RevitAddIns^>
    ) > "%APPDATA%\Autodesk\Revit\Addins\2026\MCPBridgeTab.addin"
    
    echo.
    echo ========================================
    echo DEPLOYMENT COMPLETE!
    echo ========================================
    echo.
    echo The MCP Bridge Tab has been installed.
    echo.
    echo NEXT STEPS:
    echo -----------
    echo 1. Close Revit if it's running
    echo 2. Disable the original MCP Bridge manifest:
    echo    - Go to: %APPDATA%\Autodesk\Revit\Addins\2026
    echo    - Rename RevitMCPBridge2026.addin to RevitMCPBridge2026.addin.disabled
    echo 3. Start Revit 2026
    echo 4. Look for "MCP Bridge" in the ribbon tabs
    echo.
    echo If it still appears in Add-ins, the original DLL is overriding.
) else (
    echo.
    echo COMPILATION FAILED
    echo.
    echo Trying alternative approach...
    
    REM Try without references to System.dll
    "%CSC%" /nologo /nostdlib /target:library /out:MCPBridgeTab.dll ^
        /reference:"%REVIT_PATH%\RevitAPI.dll" ^
        /reference:"%REVIT_PATH%\RevitAPIUI.dll" ^
        /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\mscorlib.dll" ^
        MCPBridgeMinimal.cs
    
    if exist MCPBridgeTab.dll (
        echo Alternative compilation succeeded!
        goto :deploy_alt
    ) else (
        echo Both compilation methods failed.
        echo The issue is likely .NET 8 compatibility.
    )
)

goto :end

:deploy_alt
echo.
echo Deploying alternative build...
copy MCPBridgeTab.dll "%APPDATA%\Autodesk\Revit\Addins\2026\" /Y
(
    echo ^<?xml version="1.0" encoding="utf-8"?^>
    echo ^<RevitAddIns^>
    echo   ^<AddIn Type="Application"^>
    echo     ^<Name^>MCP Bridge Tab Alternative^</Name^>
    echo     ^<Assembly^>%APPDATA%\Autodesk\Revit\Addins\2026\MCPBridgeTab.dll^</Assembly^>
    echo     ^<FullClassName^>MCPBridgeTab.MCPBridgeTabApp^</FullClassName^>
    echo     ^<ClientId^>DDDDDDDD-EEEE-FFFF-0000-111111111111^</ClientId^>
    echo     ^<VendorId^>MCPBridgeAlt^</VendorId^>
    echo   ^</AddIn^>
    echo ^</RevitAddIns^>
) > "%APPDATA%\Autodesk\Revit\Addins\2026\MCPBridgeTab.addin"

:end
echo.
pause