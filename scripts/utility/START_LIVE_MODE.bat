@echo off
REM Start Claude Code in LIVE mode with Revit MCP
REM Enables real-time interaction with Revit models

echo ========================================
echo   Claude Code + Revit LIVE Mode
echo ========================================
echo.

REM Check if Revit is running
echo Checking Revit status...
powershell -Command "if ((Get-Process | Where-Object {$_.ProcessName -like '*Revit*'}).Count -gt 0) { Write-Host 'OK Revit is running!' -ForegroundColor Green } else { Write-Host 'WARNING Revit not detected - start Revit first' -ForegroundColor Yellow }"
echo.

echo Starting Claude Code with Revit MCP enabled...
echo.
echo Once started, try:
echo   "Claude, ping Revit to test connection"
echo   "Claude, show me all rooms in my project"
echo   "Claude, create a room schedule"
echo.

cd /d D:\RevitMCPBridge2026
set CLAUDE_MCP_CONFIG=%USERPROFILE%\.claude\mcp-configs\revit.json
claude

