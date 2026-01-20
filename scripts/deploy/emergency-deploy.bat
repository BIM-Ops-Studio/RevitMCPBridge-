@echo off
echo Emergency MCP Bridge Deployment
echo ===============================
echo.
echo This will replace the existing MCP Bridge with a version that creates its own ribbon tab.
echo.
pause

set DLL_PATH=C:\ProgramData\Autodesk\Revit\Addins\2026
set ADDIN_PATH=%APPDATA%\Autodesk\Revit\Addins\2026

echo.
echo Step 1: Backing up existing files...
copy "%ADDIN_PATH%\RevitMCPBridge2026.dll" "%ADDIN_PATH%\RevitMCPBridge2026.dll.old" /Y
copy "%ADDIN_PATH%\RevitMCPBridge2026.addin" "%ADDIN_PATH%\RevitMCPBridge2026.addin.old" /Y

echo.
echo Step 2: Disabling old MCP Bridge...
move "%ADDIN_PATH%\RevitMCPBridge2026.addin" "%ADDIN_PATH%\RevitMCPBridge2026.addin.disabled" /Y

echo.
echo Step 3: Creating new manifest that forces ribbon tab...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>MCP Bridge 2026^</Name^>
echo     ^<Assembly^>%DLL_PATH%\RevitMCPBridge2026_New.dll^</Assembly^>
echo     ^<FullClassName^>RevitMCPBridge.RevitMCPBridgeApp^</FullClassName^>
echo     ^<ClientId^>8B8B6F55-9C7A-4F5E-8D8A-1B2C3D4E5F62^</ClientId^>
echo     ^<VendorId^>ADSK^</VendorId^>
echo     ^<VendorDescription^>MCP Bridge with Dedicated Tab^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%ADDIN_PATH%\RevitMCPBridge2026_New.addin"

echo.
echo Step 4: Instructions to complete installation:
echo.
echo 1. The old MCP Bridge has been disabled
echo 2. A new manifest has been created
echo 3. You need to build the new DLL using Visual Studio or the build scripts
echo 4. Once built, copy the DLL to: %DLL_PATH%\RevitMCPBridge2026_New.dll
echo 5. Restart Revit 2026
echo.
echo The MCP Bridge will then appear in its own ribbon tab!
echo.
pause