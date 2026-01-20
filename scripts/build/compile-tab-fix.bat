@echo off
cd /d D:\RevitMCPBridge2026
echo Compiling MCP Bridge Tab Fix...

"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /target:library /out:MCPBridgeTab.dll /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" /reference:"C:\Program Files\Autodesk\Revit 2026\RevitAPIUI.dll" MCPBridgeTab.cs

if exist MCPBridgeTab.dll (
    echo SUCCESS: Compiled MCPBridgeTab.dll
    copy MCPBridgeTab.dll "C:\ProgramData\Autodesk\Revit\Addins\2026\" /Y
    echo Copied to Revit addins folder
) else (
    echo FAILED: Could not compile
    pause
)
