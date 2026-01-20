@echo off
echo Copying updated RevitMCPBridge2026.dll...
copy /Y "D:\RevitMCPBridge2026\bin\Release\RevitMCPBridge2026.dll" "%APPDATA%\Autodesk\Revit\Addins\2026\"
if %errorlevel% == 0 (
    echo SUCCESS: DLL copied successfully!
    echo.
    echo Now restart Revit and open your model.
) else (
    echo ERROR: Failed to copy DLL. Make sure Revit is closed.
)
pause
