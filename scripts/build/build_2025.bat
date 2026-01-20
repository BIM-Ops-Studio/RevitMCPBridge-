@echo off
echo Building RevitMCPBridge2025...
dotnet build RevitMCPBridge2025.csproj -c Release
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful! Deploying to Revit 2025 addins folder...
    copy /Y "bin\Release2025\RevitMCPBridge2025.dll" "C:\ProgramData\Autodesk\Revit\Addins\2025\"
    copy /Y "bin\Release2025\Serilog.dll" "C:\ProgramData\Autodesk\Revit\Addins\2025\"
    copy /Y "bin\Release2025\Serilog.Sinks.File.dll" "C:\ProgramData\Autodesk\Revit\Addins\2025\"
    copy /Y "RevitMCPBridge2025.addin" "C:\ProgramData\Autodesk\Revit\Addins\2025\"
    echo.
    echo Deployment complete! Restart Revit 2025 to load the updated add-in.
) else (
    echo.
    echo Build failed! Check errors above.
)
pause
