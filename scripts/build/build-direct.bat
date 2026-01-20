@echo off
echo Direct compilation of MCP Bridge...

set CSC="C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
set OUTPUT=bin\Debug\RevitMCPBridge2026.dll

if not exist bin\Debug mkdir bin\Debug

%CSC% /target:library /out:%OUTPUT% ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" ^
    /reference:"C:\Program Files\Autodesk\Revit 2026\AdWindows.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Windows.Forms.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WindowsBase.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\PresentationCore.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\PresentationFramework.dll" ^
    /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Xaml.dll" ^
    src\RevitMCPBridgeApp-Simple.cs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Output: %OUTPUT%
) else (
    echo.
    echo Build failed!
)

pause