@echo off
echo Compiling Final MCP Bridge Tab DLL
echo ==================================
echo.

cd /d D:\RevitMCPBridge2026

set CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
set REVIT_PATH=C:\Program Files\Autodesk\Revit 2026

REM Clean compile - just the one file we need
echo Compiling MCPBridgeTabOnly.cs...

"%CSC%" /nologo /target:library /out:MCPBridgeTabFinal.dll ^
    /reference:"%REVIT_PATH%\RevitAPI.dll" ^
    /reference:"%REVIT_PATH%\RevitAPIUI.dll" ^
    /reference:System.dll ^
    MCPBridgeTabOnly.cs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! MCPBridgeTabFinal.dll created
    echo.
    echo Deploying...
    copy MCPBridgeTabFinal.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    
    echo.
    echo Creating manifest...
    (
        echo ^<?xml version="1.0" encoding="utf-8"?^>
        echo ^<RevitAddIns^>
        echo   ^<AddIn Type="Application"^>
        echo     ^<Name^>MCP Bridge Tab^</Name^>
        echo     ^<Assembly^>C:\ProgramData\Autodesk\Revit\Addins\2026\MCPBridgeTabFinal.dll^</Assembly^>
        echo     ^<FullClassName^>MCPBridgeTab.MCPBridgeTabApp^</FullClassName^>
        echo     ^<ClientId^>98765432-FEDC-BA98-7654-321098765432^</ClientId^>
        echo     ^<VendorId^>MCPBridge^</VendorId^>
        echo   ^</AddIn^>
        echo ^</RevitAddIns^>
    ) > "%APPDATA%\Autodesk\Revit\Addins\2026\MCPBridgeTabFinal.addin"
    
    echo.
    echo ========================================
    echo DEPLOYMENT COMPLETE!
    echo ========================================
    echo.
    echo The new MCP Bridge Tab has been installed.
    echo.
    echo IMPORTANT: Make sure to disable any other MCP Bridge addins
    echo to avoid conflicts. Check for:
    echo - RevitMCPBridge2026.addin
    echo - MCPBridge_Tab.addin
    echo - MCPBridgeTab.addin
    echo.
    echo Restart Revit 2026 to see the MCP Bridge in its own tab!
) else (
    echo.
    echo COMPILATION FAILED
    echo Check that Revit 2026 is installed correctly.
)

pause